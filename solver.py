"""
🧠 TIMETABLE SOLVER — Baby-level explanation
============================================
This uses Google's OR-Tools (a constraint solver) to put subjects into time slots.
Rules:
1. A teacher can't be in two places at once.
2. A class can't have two subjects at the same time.
3. Every subject must get its weekly periods.
4. Breaks stay empty.

We create "decision variables" — like little switches that are either ON or OFF.
Each switch = "Does class X have subject Y in day D, period P?"
The solver flips switches until all rules are happy.
"""

import math
from typing import Dict, List, Optional, Tuple, Any

from ortools.sat.python import cp_model

from models import Class, Teacher, SchoolConfig, ClassPriorityConfig, get_all_slots


# ---------------------------------------------------------------------------
# PHASE 1: CORE CONSTRAINT SOLVER
# ---------------------------------------------------------------------------


def build_class_subject_teacher_map(classes: List[Class]) -> Dict[Tuple[str, str], str]:
    """
    Maps (class_id, subject) -> teacher_id.
    Like a lookup table: "Who teaches Math to 5A?" -> "T1"
    """
    m = {}
    for c in classes:
        for cs in c.subjects:
            m[(c.class_id, cs.subject)] = cs.teacher_id
    return m


    """
    solver.py — Timetable logic for Timable
    """
    from typing import List, Dict, Tuple
    from models import Class, Teacher, SchoolConfig

    def build_timetable(classes: List[Class], teachers: List[Teacher], config: SchoolConfig) -> Dict[Tuple[str, int, int], Tuple[str, str]]:
        """
        Build a timetable: (class_id, day_idx, period_idx) -> (subject, teacher_id)
        Simple greedy algorithm: fill periods for each class, assign teachers if available.
        """
        timetable = {}
        teacher_load = {t.id: {d: 0 for d in range(len(config.days))} for t in teachers}
        for c in classes:
            periods_needed = []
            for subj in c.subjects:
                for _ in range(subj.weekly_periods):
                    periods_needed.append((subj.subject, subj.teacher_id))
            slot_idx = 0
            for d in range(len(config.days)):
                for p in range(config.periods_per_day):
                    if slot_idx >= len(periods_needed):
                        break
                    if p in config.break_periods:
                        continue
                    subject, teacher_id = periods_needed[slot_idx]
                    # Check teacher load
                    if teacher_load[teacher_id][d] < next((t.max_periods_per_day for t in teachers if t.id == teacher_id), 6):
                        timetable[(c.id, d, p)] = (subject, teacher_id)
                        teacher_load[teacher_id][d] += 1
                        slot_idx += 1
        return timetable
def solve_timetable(
    config: SchoolConfig,
    teachers: List[Teacher],
    classes: List[Class],
) -> Optional[Dict[Tuple[str, int, int], Tuple[str, str]]]:
    """
    Solves the timetable. Returns a dict:
    (class_id, day_idx, period_idx) -> (subject, teacher_id)
    or None if no solution exists.
    """
    model = cp_model.CpModel()
    days = config.days
    num_days = len(days)
    num_periods = config.periods_per_day
    breaks = set(config.break_period_indices)
    available_periods_per_day = max(0, num_periods - len(breaks))

    # Build mapping: (class_id, subject) -> weekly_periods, teacher_id
    class_subject_info: Dict[Tuple[str, str], Tuple[int, str]] = {}
    for c in classes:
        for cs in c.subjects:
            class_subject_info[(c.class_id, cs.subject)] = (cs.weekly_periods, cs.teacher_id)

    # All classes and their subjects
    class_ids = [c.class_id for c in classes]
    teacher_ids = [t.teacher_id for t in teachers]

    # Create boolean variable: assign[class_id, subject, day, period] = 1 if scheduled
    assign = {}
    for (cid, subj), (weekly, _) in class_subject_info.items():
        for d in range(num_days):
            for p in range(num_periods):
                if p in breaks:
                    continue
                key = (cid, subj, d, p)
                assign[key] = model.NewBoolVar(f"assign_{cid}_{subj}_{d}_{p}")

    # Constraint 1: Each (class, subject) gets exactly weekly_periods slots
    for (cid, subj), (weekly, _) in class_subject_info.items():
        model.Add(
            sum(
                assign.get((cid, subj, d, p), 0)
                for d in range(num_days)
                for p in range(num_periods)
                if p not in breaks
            )
            == weekly
        )

    # Constraint 2: Each class has at most 1 subject per (day, period)
    for cid in class_ids:
        for d in range(num_days):
            for p in range(num_periods):
                if p in breaks:
                    continue
                vars_here = [
                    assign[(cid, subj, d, p)]
                    for (c, subj) in class_subject_info
                    if c == cid
                ]
                if vars_here:
                    model.Add(sum(vars_here) <= 1)

    # Constraint 3: Each teacher has at most 1 assignment per (day, period)
    for tid in teacher_ids:
        for d in range(num_days):
            for p in range(num_periods):
                if p in breaks:
                    continue
                vars_here = [
                    assign[(cid, subj, d, p)]
                    for (cid, subj), (_, t) in class_subject_info.items()
                    if t == tid
                ]
                if vars_here:
                    model.Add(sum(vars_here) <= 1)

    # Teacher weekly load -> relax daily capacity if data demands more
    teacher_weekly_load: Dict[str, int] = {tid: 0 for tid in teacher_ids}
    for (_, _), (weekly, tid) in class_subject_info.items():
        teacher_weekly_load[tid] = teacher_weekly_load.get(tid, 0) + weekly

    effective_teacher_limits: Dict[str, int] = {}
    for t in teachers:
        weekly_load = teacher_weekly_load.get(t.teacher_id, 0)
        required_daily = math.ceil(weekly_load / num_days) if num_days else 0
        relaxed_cap = max(t.max_periods_per_day, required_daily)
        if available_periods_per_day:
            relaxed_cap = min(relaxed_cap, available_periods_per_day)
        effective_teacher_limits[t.teacher_id] = relaxed_cap

    # Constraint 4: Max periods per day for each teacher (auto-relaxed)
    for t in teachers:
        for d in range(num_days):
            vars_this_day = [
                assign[(cid, subj, d, p)]
                for (cid, subj), (_, tid) in class_subject_info.items()
                if tid == t.teacher_id
                for p in range(num_periods)
                if p not in breaks
            ]
            if vars_this_day:
                model.Add(sum(vars_this_day) <= effective_teacher_limits[t.teacher_id])

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    # Build result: (class_id, day_idx, period_idx) -> (subject, teacher_id)
    result: Dict[Tuple[str, int, int], Tuple[str, str]] = {}
    for (cid, subj, d, p), var in assign.items():
        if solver.Value(var) == 1:
            _, teacher_id = class_subject_info[(cid, subj)]
            result[(cid, d, p)] = (subj, teacher_id)

    return result


def invert_to_teacher_timetable(
    class_timetable: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
) -> Dict[str, Dict[Tuple[int, int], Tuple[str, str]]]:
    """
    "Inverts" the class timetable: for each teacher, we list their (day, period) -> (class, subject).
    Like flipping a class schedule to see it from the teacher's perspective.
    """
    teacher_schedules: Dict[str, Dict[Tuple[int, int], Tuple[str, str]]] = {}
    for (cid, d, p), (subj, tid) in class_timetable.items():
        if tid not in teacher_schedules:
            teacher_schedules[tid] = {}
        teacher_schedules[tid][(d, p)] = (cid, subj)
    return teacher_schedules


# ---------------------------------------------------------------------------
# PHASE 2: PRIORITY-BASED SCORING AND IMPROVEMENT
# ---------------------------------------------------------------------------


def compute_timetable_score(
    class_timetable: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
    priority_configs: List[ClassPriorityConfig],
) -> float:
    """
    Higher score = better timetable.
    - Bonus: priority subjects in early periods (periods 0,1,2)
    - Penalty: back-to-back heavy subjects
    """
    num_periods = config.periods_per_day
    breaks = set(config.break_period_indices)
    priority_map = {pc.class_id: pc for pc in priority_configs}

    score = 0.0

    for (cid, d, p), (subj, _) in class_timetable.items():
        pc = priority_map.get(cid)
        if not pc:
            continue
        if subj in pc.priority_subjects:
            # Early periods (0,1,2) get bonus; later periods get less
            early_bonus = max(0, 3 - p)
            score += early_bonus

    # Penalty: back-to-back heavy subjects
    for cid in {k[0] for k in class_timetable}:
        pc = priority_map.get(cid)
        if not pc or not pc.heavy_subjects:
            continue
        heavy = set(pc.heavy_subjects)
        for d in range(len(config.days)):
            periods_this_day = [
                p for p in range(num_periods)
                if p not in breaks
                and (cid, d, p) in class_timetable
                and class_timetable[(cid, d, p)][0] in heavy
            ]
            for i in range(len(periods_this_day) - 1):
                if periods_this_day[i + 1] == periods_this_day[i] + 1:
                    score -= 2.0  # Back-to-back heavy penalty

    return score


def try_swap(
    class_timetable: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
    class_subject_info: Dict[Tuple[str, str], Tuple[int, str]],
) -> Optional[Dict[Tuple[str, int, int], Tuple[str, str]]]:
    """
    Try swapping two slots for the same class. If valid (no constraint break), return new timetable.
    """
    import copy
    slots = list(class_timetable.keys())
    if len(slots) < 2:
        return None

    # Pick two random slots from same class
    import random
    cid_to_slots = {}
    for k in slots:
        cid = k[0]
        if cid not in cid_to_slots:
            cid_to_slots[cid] = []
        cid_to_slots[cid].append(k)

    for cid, cslots in cid_to_slots.items():
        if len(cslots) < 2:
            continue
        a, b = random.sample(cslots, 2)
        new_tt = copy.deepcopy(class_timetable)
        subj_a, tid_a = new_tt[a]
        subj_b, tid_b = new_tt[b]
        new_tt[a] = (subj_b, tid_b)
        new_tt[b] = (subj_a, tid_a)
        if is_valid_swap(new_tt, config, class_subject_info):
            return new_tt
    return None


def is_valid_swap(
    tt: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
    class_subject_info: Dict[Tuple[str, str], Tuple[int, str]],
) -> bool:
    """Check teacher and class constraints still hold after swap."""
    teacher_slots: Dict[str, Dict[Tuple[int, int], Tuple[str, str]]] = {}
    for (cid, d, p), (subj, tid) in tt.items():
        if tid not in teacher_slots:
            teacher_slots[tid] = {}
        if (d, p) in teacher_slots[tid]:
            return False  # Teacher clash
        teacher_slots[tid][(d, p)] = (cid, subj)

    # Check weekly periods
    from collections import Counter
    counts: Dict[Tuple[str, str], int] = {}
    for (cid, d, p), (subj, _) in tt.items():
        k = (cid, subj)
        counts[k] = counts.get(k, 0) + 1
    for (cid, subj), count in counts.items():
        req, _ = class_subject_info.get((cid, subj), (0, ""))
        if count != req:
            return False
    return True


def improve_timetable(
    class_timetable: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
    classes: List[Class],
    priority_configs: List[ClassPriorityConfig],
    max_iters: int = 100,
) -> Dict[Tuple[str, int, int], Tuple[str, str]]:
    """
    Try swaps to improve score. Keep best.
    """
    class_subject_info = {}
    for c in classes:
        for cs in c.subjects:
            class_subject_info[(c.class_id, cs.subject)] = (cs.weekly_periods, cs.teacher_id)

    best = dict(class_timetable)
    best_score = compute_timetable_score(best, config, priority_configs)

    for _ in range(max_iters):
        swapped = try_swap(best, config, class_subject_info)
        if swapped is None:
            continue
        new_score = compute_timetable_score(swapped, config, priority_configs)
        if new_score > best_score:
            best = swapped
            best_score = new_score

    return best


# ---------------------------------------------------------------------------
# PHASE 3: WEEKLY ROTATION
# ---------------------------------------------------------------------------


def rotate_timetable(
    class_timetable: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
    shift_days: int,
) -> Dict[Tuple[str, int, int], Tuple[str, str]]:
    """
    Shifts each class's schedule by shift_days. Day 0 becomes day (0+shift)%num_days.
    Keeps the same pattern but rotated.
    """
    num_days = len(config.days)
    rotated = {}
    for (cid, d, p), (subj, tid) in class_timetable.items():
        new_d = (d + shift_days) % num_days
        rotated[(cid, new_d, p)] = (subj, tid)
    return rotated


def generate_rotations(
    class_timetable: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
    num_weeks: int = 3,
) -> List[Dict[Tuple[str, int, int], Tuple[str, str]]]:
    """
    Generates num_weeks rotations (Week 1 = original, Week 2 = shift 1, etc.)
    """
    result = [dict(class_timetable)]
    for s in range(1, num_weeks):
        result.append(rotate_timetable(class_timetable, config, s))
    return result
