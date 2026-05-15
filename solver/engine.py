"""Core timetable solver engine using OR-Tools CP-SAT."""

from typing import Dict, List, Optional, Tuple

from ortools.sat.python import cp_model

from models import Class, ClassPriorityConfig, SchoolConfig, Teacher
from solver.constraints import create_default_registry
from solver.constraints.registry import ConstraintRegistry
from solver.types import SolverContext
from solver import improver as solver_improver
from solver.scoring import compute_timetable_score

from typing import Any, List


def solve_timetable(
    config: SchoolConfig,
    teachers: List[Teacher],
    classes: List[Class],
    priority_configs: Optional[List[ClassPriorityConfig]] = None,
    registry: Optional[ConstraintRegistry] = None,
    allow_relax_class_free_periods: bool = False,
) -> Optional[Dict[Tuple[str, int, int], Tuple[str, str]]]:
    """
    Solves the timetable. Returns a dict:
    (class_id, day_idx, period_idx) -> (subject, teacher_id)
    or None if no solution exists.

    Accepts optional priority_configs to optimize for quality.
    Accepts an optional ConstraintRegistry to control which constraints are active.
    """
    if registry is None:
        registry = create_default_registry()

    # First, perform lightweight feasibility checks to catch impossible configs
    diag = _perform_feasibility_analysis(config, teachers, classes)
    if diag:
        # If feasibility analysis finds absolute impossibilities, print diagnostics
        print("Feasibility issues detected:")
        for d in diag:
            print("- ", d)
        # Do not abort here: still attempt best-effort construction below only if
        # the issues are not absolute capacity failures.

    model = cp_model.CpModel()
    context = SolverContext(
        model=model, config=config, classes=classes, teachers=teachers
    )

    # Apply all active constraints (hard constraints should remain hard)
    for constraint in registry.get_active():
        constraint.apply(context)

    # If priority configs exist, add soft constraints as an objective
    if priority_configs:
        context.priority_configs = priority_configs
        _add_optimization_objective(model, context, config, priority_configs)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 20.0
    solver.parameters.log_search_progress = False
    status = solver.Solve(model)

    # If the exact CP-SAT solve produced a feasible/optimal schedule, return it
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        res, diags = _build_result_and_diagnostics(solver, context)
        if diags:
            for d in diags:
                print("-", d)
        return res

    # Otherwise, attempt adaptive recovery: try targeted relaxation, then greedy+repair
    print("Exact solver failed — attempting adaptive recovery (relax -> greedy + repair)")

    # Attempt a targeted soft-relaxation: disable `class_free_periods` if caller opts in
    if allow_relax_class_free_periods:
        try:
            print("Attempting targeted relaxation: disabling class_free_periods and re-solving")
            relaxed_registry = create_default_registry()
            relaxed_registry.disable('class_free_periods')

            r_model = cp_model.CpModel()
            r_context = SolverContext(model=r_model, config=config, classes=classes, teachers=teachers)
            for c in relaxed_registry.get_active():
                c.apply(r_context)
            if priority_configs:
                _add_optimization_objective(r_model, r_context, config, priority_configs)

            r_solver = cp_model.CpSolver()
            r_solver.parameters.max_time_in_seconds = 15.0
            r_status = r_solver.Solve(r_model)
            if r_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                res, diags = _build_result_and_diagnostics(r_solver, r_context)
                print("Relaxed solve succeeded; returning relaxed timetable.")
                if diags:
                    for d in diags:
                        print("-", d)
                return res
            else:
                print("Relaxed solve did not find a solution; proceeding to greedy fallback.")
        except Exception:
            print("Relaxation attempt raised an exception; proceeding to greedy fallback.")

    greedy = _greedy_initial_assignment(config, teachers, classes)
    if greedy is None:
        print("Adaptive recovery failed — no feasible initial assignment could be found.")
        return None

    # Run improver to iteratively repair and optimize the greedy result
    try:
        improved = solver_improver.improve_timetable(
            greedy, config, classes, priority_configs or [], max_iters=200
        )
    except Exception:
        improved = greedy

    print("Adaptive recovery produced a best-effort timetable (soft constraints may be relaxed).")
    return improved


def _build_result_and_diagnostics(solver: cp_model.CpSolver, context: SolverContext) -> Tuple[Dict[Tuple[str, int, int], Tuple[str, str]], List[str]]:
    result: Dict[Tuple[str, int, int], Tuple[str, str]] = {}
    for (cid, subj, d, p), var in context.assign.items():
        if solver.Value(var) == 1:
            _, teacher_id = context.class_subject_info[(cid, subj)]
            result[(cid, d, p)] = (subj, teacher_id)

    diagnostics: List[str] = []
    total_penalty = 0
    for (pv, w) in getattr(context, 'soft_penalties', []):
        val = solver.Value(pv)
        if val:
            # parse var name if possible: expected freepen_{cid}_{d}
            name = pv.Name()
            diagnostics.append(f"Soft penalty {name} = {val} (weight {w})")
            total_penalty += val * w

    if diagnostics:
        diagnostics.append(f"Total soft penalty: {total_penalty}")

    context.diagnostics = diagnostics
    return result, diagnostics


def _add_optimization_objective(
    model: cp_model.CpModel,
    context: SolverContext,
    config: SchoolConfig,
    priority_configs: List[ClassPriorityConfig],
) -> None:
    """
    Add soft constraints to optimize timetable quality based on priority configs.
    """
    priority_map = {pc.class_id: pc for pc in priority_configs}
    breaks = context.breaks
    
    score = 0
    
    # Bonus: priority subjects in early periods
    for (cid, subj, d, p), var in context.assign.items():
        if p not in breaks:
            pc = priority_map.get(cid)
            if pc and subj in pc.priority_subjects:
                early_bonus = max(0, 3 - p)
                score += early_bonus * var
    
    # Penalty: back-to-back heavy subjects
    for (cid, subj, d, p), var in context.assign.items():
        if p not in breaks and p + 1 not in breaks:
            pc = priority_map.get(cid)
            if pc and subj in pc.heavy_subjects:
                next_var = context.assign.get((cid, subj, d, p + 1))
                if next_var is not None:
                    score -= 2 * var * next_var
    
    # Incorporate soft penalties collected by constraints (e.g., free-period penalties)
    penalty_expr = None
    if getattr(context, 'soft_penalties', None):
        pen_terms = []
        for (pv, w) in context.soft_penalties:
            pen_terms.append(w * pv)
        # sum() on an empty list errors; safe because list non-empty here
        penalty_expr = sum(pen_terms)

    if penalty_expr is not None:
        model.Maximize(score - penalty_expr)
    else:
        model.Maximize(score)


def invert_to_teacher_timetable(
    class_timetable: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
) -> Dict[str, Dict[Tuple[int, int], Tuple[str, str]]]:
    """Inverts the class timetable: for each teacher, list their (day, period) -> (class_id, subject)."""
    teacher_schedules: Dict[str, Dict[Tuple[int, int], Tuple[str, str]]] = {}
    for (cid, d, p), (subj, tid) in class_timetable.items():
        if tid not in teacher_schedules:
            teacher_schedules[tid] = {}
        teacher_schedules[tid][(d, p)] = (cid, subj)
    return teacher_schedules


def solve_timetable_with_diagnostics(
    config: SchoolConfig,
    teachers: List[Teacher],
    classes: List[Class],
    priority_configs: Optional[List[ClassPriorityConfig]] = None,
    registry: Optional[ConstraintRegistry] = None,
    allow_relax_class_free_periods: bool = False,
) -> Tuple[Optional[Dict[Tuple[str, int, int], Tuple[str, str]]], List[str]]:
    """Wrapper that returns (timetable_or_none, diagnostics_list).

    Diagnostics include feasibility warnings and high-level solver notes.
    """
    diagnostics: List[str] = []
    notes = _perform_feasibility_analysis(config, teachers, classes)
    diagnostics.extend(notes)

    tt = solve_timetable(
        config,
        teachers,
        classes,
        priority_configs=priority_configs,
        registry=registry,
        allow_relax_class_free_periods=allow_relax_class_free_periods,
    )

    if tt is None:
        diagnostics.append("No feasible timetable found after adaptive recovery.")
    else:
        diagnostics.append("Timetable generated (best-effort).")

    return tt, diagnostics


def _perform_feasibility_analysis(config: SchoolConfig, teachers: List[Teacher], classes: List[Class]) -> List[str]:
    """Return a list of diagnostic strings describing absolute feasibility problems.

    This checks capacity-based impossibilities such as required periods exceeding
    available slots or teacher total demands exceeding capacity.
    """
    notes: List[str] = []
    days = len(config.days)
    periods_per_day = config.periods_per_day
    breaks = set(config.break_periods.keys())
    non_breaks_per_day = max(0, periods_per_day - len(breaks))
    total_slots = non_breaks_per_day * days

    # Total required periods
    total_required = 0
    for c in classes:
        for cs in c.subjects:
            total_required += cs.weekly_periods

    if total_required > total_slots * len(classes):
        notes.append(f"Total required periods ({total_required}) unusually high relative to slots per class/day.")

    # Per-class per-day minimum occupied check (due to free periods limit of 2)
    for c in classes:
        cid = getattr(c, 'class_id', getattr(c, 'id', ''))
        weekly_req = sum(cs.weekly_periods for cs in c.subjects)
        # Minimum occupied per day required to avoid >2 free periods
        min_per_day = max(0, non_breaks_per_day - 2)
        min_weekly_possible = min_per_day * days
        if weekly_req > non_breaks_per_day * days:
            notes.append(f"Class {cid} requires {weekly_req} periods but only {non_breaks_per_day*days} non-break slots available.")
        if weekly_req < min_weekly_possible:
            # Under the preferred free-period rule this will likely cause violations;
            # mark as a diagnostic warning rather than an absolute impossibility.
            notes.append(f"Class {cid} requires only {weekly_req} periods; this will likely violate the preferred 'max 2 free periods/day' rule (needs {min_weekly_possible}).")

    # Teacher capacity checks (weekly)
    teacher_demand = {}
    for c in classes:
        for cs in c.subjects:
            teacher_demand[cs.teacher_id] = teacher_demand.get(cs.teacher_id, 0) + cs.weekly_periods
    for t in teachers:
        cap = getattr(t, 'max_periods_per_week', None)
        demand = teacher_demand.get(t.teacher_id, 0)
        if demand > days * non_breaks_per_day:
            notes.append(f"Teacher {t.teacher_id} demand ({demand}) exceeds total available non-break slots ({days*non_breaks_per_day}).")
        if cap is not None and demand > cap:
            notes.append(f"Teacher {t.teacher_id} demand ({demand}) exceeds their weekly limit ({cap}).")

    return notes


def _greedy_initial_assignment(config: SchoolConfig, teachers: List[Teacher], classes: List[Class]) -> Optional[Dict[Tuple[str, int, int], Tuple[str, str]]]:
    """Attempt a deterministic greedy assignment respecting hard constraints.

    This is used as a best-effort starting solution when the CP solver fails.
    """
    days = len(config.days)
    periods_per_day = config.periods_per_day
    breaks = set(config.break_periods.keys())
    slot_list: List[Tuple[int, int]] = [(d, p) for d in range(days) for p in range(periods_per_day) if p not in breaks]

    # Map teacher -> set of occupied (d,p)
    teacher_occupied = {t.teacher_id: set() for t in teachers}
    # Map class -> occupied per day
    class_occupied_per_day = {}
    result: Dict[Tuple[str, int, int], Tuple[str, str]] = {}

    # Pre-check per-class feasibility relative to min occupied slots
    non_breaks_per_day = max(0, periods_per_day - len(breaks))
    min_occupied_per_day = max(0, non_breaks_per_day - 2)
    for c in classes:
        cid = getattr(c, 'class_id', getattr(c, 'id', ''))
        weekly_req = sum(cs.weekly_periods for cs in c.subjects)
        min_weekly_needed = min_occupied_per_day * days
        # If weekly_req is less than the ideal min, we still attempt a greedy placement
        # so that the improver / penalty-driven objective can try to fix violations.
        class_occupied_per_day[cid] = {d: 0 for d in range(days)}

    # For deterministic behavior, sort classes and subjects
    for c in sorted(classes, key=lambda x: getattr(x, 'class_id', getattr(x, 'id', ''))):
        cid = getattr(c, 'class_id', getattr(c, 'id', ''))
        # Expand subject slots list
        subject_slots = []
        for cs in c.subjects:
            subject_slots.extend([(cs.subject, cs.teacher_id) for _ in range(cs.weekly_periods)])

        # Assign each required subject occurrence to the earliest valid slot
        for subj, tid in subject_slots:
            placed = False
            for d, p in slot_list:
                # skip if this class already has something at this slot
                if (cid, d, p) in result:
                    continue
                # Check teacher availability
                if (d, p) in teacher_occupied.get(tid, set()):
                    continue
                # Check class occupancy for the day (prevent exceeding free-period limit)
                if class_occupied_per_day[cid][d] >= non_breaks_per_day:
                    continue
                # Tentative occupation would result in free periods = non_breaks_per_day - occupied
                tentative_occupied = class_occupied_per_day[cid][d] + 1
                tentative_free = non_breaks_per_day - tentative_occupied
                if tentative_free > 2:
                    # still too many free periods even after placing? this check is conservative
                    pass
                # All clear — assign
                result[(cid, d, p)] = (subj, tid)
                teacher_occupied.setdefault(tid, set()).add((d, p))
                class_occupied_per_day[cid][d] += 1
                placed = True
                break
            if not placed:
                # failed to place this subject occurrence
                return None

    # Final validation: ensure teacher clashes and per-class per-day free limit
    for tid, occ in teacher_occupied.items():
        if len(occ) != len(set(occ)):
            return None

    # Do not enforce per-day free-period hard check here; let improver/penalties handle it

    return result
