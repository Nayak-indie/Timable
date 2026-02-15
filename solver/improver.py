"""Post-solve improvement via random swaps."""

import copy
import random
from typing import Dict, List, Optional, Tuple

from models import Class, ClassPriorityConfig, SchoolConfig
from solver.scoring import compute_timetable_score


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
    counts: Dict[Tuple[str, str], int] = {}
    for (cid, d, p), (subj, _) in tt.items():
        k = (cid, subj)
        counts[k] = counts.get(k, 0) + 1
    for (cid, subj), count in counts.items():
        req, _ = class_subject_info.get((cid, subj), (0, ""))
        if count != req:
            return False
    return True


def try_swap(
    class_timetable: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
    class_subject_info: Dict[Tuple[str, str], Tuple[int, str]],
) -> Optional[Dict[Tuple[str, int, int], Tuple[str, str]]]:
    """
    Try swapping two slots for the same class. If valid, return new timetable.
    """
    slots = list(class_timetable.keys())
    if len(slots) < 2:
        return None

    cid_to_slots: Dict[str, List] = {}
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


def improve_timetable(
    class_timetable: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
    classes: List[Class],
    priority_configs: List[ClassPriorityConfig],
    max_iters: int = 100,
) -> Dict[Tuple[str, int, int], Tuple[str, str]]:
    """Try swaps to improve score. Keep best."""
    class_subject_info = {}
    for c in classes:
        for cs in c.subjects:
            class_subject_info[(c.class_id, cs.subject)] = (
                cs.weekly_periods,
                cs.teacher_id,
            )

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
