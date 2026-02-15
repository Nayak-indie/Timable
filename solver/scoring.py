"""Timetable scoring logic, separated from constraint model."""

from typing import Dict, List, Tuple

from models import ClassPriorityConfig, SchoolConfig


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
                p
                for p in range(num_periods)
                if p not in breaks
                and (cid, d, p) in class_timetable
                and class_timetable[(cid, d, p)][0] in heavy
            ]
            for i in range(len(periods_this_day) - 1):
                if periods_this_day[i + 1] == periods_this_day[i] + 1:
                    score -= 2.0

    return score
