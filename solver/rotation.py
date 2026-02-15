"""Weekly timetable rotation."""

from typing import Dict, List, Tuple

from models import SchoolConfig


def rotate_timetable(
    class_timetable: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
    shift_days: int,
) -> Dict[Tuple[str, int, int], Tuple[str, str]]:
    """Shifts each class's schedule by shift_days."""
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
    """Generates num_weeks rotations (Week 1 = original, Week 2 = shift 1, etc.)"""
    result = [dict(class_timetable)]
    for s in range(1, num_weeks):
        result.append(rotate_timetable(class_timetable, config, s))
    return result
