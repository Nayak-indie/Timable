"""Core timetable solver engine using OR-Tools CP-SAT."""

from typing import Dict, List, Optional, Tuple

from ortools.sat.python import cp_model

from models import Class, ClassPriorityConfig, SchoolConfig, Teacher
from solver.constraints import create_default_registry
from solver.constraints.registry import ConstraintRegistry
from solver.types import SolverContext


def solve_timetable(
    config: SchoolConfig,
    teachers: List[Teacher],
    classes: List[Class],
    priority_configs: Optional[List[ClassPriorityConfig]] = None,
    registry: Optional[ConstraintRegistry] = None,
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

    model = cp_model.CpModel()
    context = SolverContext(
        model=model, config=config, classes=classes, teachers=teachers
    )

    # Apply all active constraints
    for constraint in registry.get_active():
        constraint.apply(context)

    # If priority configs exist, add soft constraints to optimize quality
    if priority_configs:
        _add_optimization_objective(model, context, config, priority_configs)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    solver.parameters.log_search_progress = False
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    # Build result
    result: Dict[Tuple[str, int, int], Tuple[str, str]] = {}
    for (cid, subj, d, p), var in context.assign.items():
        if solver.Value(var) == 1:
            _, teacher_id = context.class_subject_info[(cid, subj)]
            result[(cid, d, p)] = (subj, teacher_id)

    return result


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
