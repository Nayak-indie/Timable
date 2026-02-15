"""Hard constraint: each teacher has at most 1 assignment per (day, period)."""

from solver.constraints.base import Constraint
from solver.types import SolverContext


class TeacherClashConstraint(Constraint):
    name = "teacher_clash"
    is_hard = True

    def apply(self, context: SolverContext) -> None:
        for tid in context.teacher_ids:
            for d in range(context.num_days):
                for p in range(context.num_periods):
                    if p in context.breaks:
                        continue
                    vars_here = [
                        context.assign[(cid, subj, d, p)]
                        for (cid, subj), (_, t) in context.class_subject_info.items()
                        if t == tid
                    ]
                    if vars_here:
                        context.model.Add(sum(vars_here) <= 1)
