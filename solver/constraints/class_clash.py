"""Hard constraint: each class has at most 1 subject per (day, period)."""

from solver.constraints.base import Constraint
from solver.types import SolverContext


class ClassClashConstraint(Constraint):
    name = "class_clash"
    is_hard = True

    def apply(self, context: SolverContext) -> None:
        for cid in context.class_ids:
            for d in range(context.num_days):
                for p in range(context.num_periods):
                    if p in context.breaks:
                        continue
                    vars_here = [
                        context.assign[(cid, subj, d, p)]
                        for (c, subj) in context.class_subject_info
                        if c == cid
                    ]
                    if vars_here:
                        context.model.Add(sum(vars_here) <= 1)
