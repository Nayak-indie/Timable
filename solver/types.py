"""Shared types for the solver package."""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from ortools.sat.python import cp_model

from models import Class, SchoolConfig, Teacher


@dataclass
class SolverContext:
    """All shared state needed by constraint modules."""

    model: cp_model.CpModel
    config: SchoolConfig
    classes: List[Class]
    teachers: List[Teacher]

    # (class_id, subject) -> (weekly_periods, teacher_id)
    class_subject_info: Dict[Tuple[str, str], Tuple[int, str]] = field(
        default_factory=dict
    )

    # (class_id, subject, day, period) -> BoolVar
    assign: Dict[Tuple[str, str, int, int], "cp_model.IntVar"] = field(
        default_factory=dict
    )

    num_days: int = 0
    num_periods: int = 0
    breaks: Set[int] = field(default_factory=set)
    class_ids: List[str] = field(default_factory=list)
    teacher_ids: List[str] = field(default_factory=list)

    # teacher_id -> effective daily limit (auto-relaxed)
    effective_teacher_limits: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        self.num_days = len(self.config.days)
        self.num_periods = self.config.periods_per_day
        self.breaks = set(self.config.break_period_indices)
        self.class_ids = [c.class_id for c in self.classes]
        self.teacher_ids = [t.teacher_id for t in self.teachers]

        available_periods_per_day = max(0, self.num_periods - len(self.breaks))

        # Build class_subject_info
        for c in self.classes:
            for cs in c.subjects:
                self.class_subject_info[(c.class_id, cs.subject)] = (
                    cs.weekly_periods,
                    cs.teacher_id,
                )

        # Create assign variables
        for (cid, subj), (weekly, _) in self.class_subject_info.items():
            for d in range(self.num_days):
                for p in range(self.num_periods):
                    if p in self.breaks:
                        continue
                    self.assign[(cid, subj, d, p)] = self.model.NewBoolVar(
                        f"assign_{cid}_{subj}_{d}_{p}"
                    )

        # Compute effective teacher limits
        teacher_weekly_load: Dict[str, int] = {tid: 0 for tid in self.teacher_ids}
        for (_, _), (weekly, tid) in self.class_subject_info.items():
            teacher_weekly_load[tid] = teacher_weekly_load.get(tid, 0) + weekly

        for t in self.teachers:
            weekly_load = teacher_weekly_load.get(t.teacher_id, 0)
            required_daily = (
                math.ceil(weekly_load / self.num_days) if self.num_days else 0
            )
            relaxed_cap = max(t.max_periods_per_day, required_daily)
            if available_periods_per_day:
                relaxed_cap = min(relaxed_cap, available_periods_per_day)
            self.effective_teacher_limits[t.teacher_id] = relaxed_cap
