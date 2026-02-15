"""Hard constraint: each (class, subject) gets exactly its required weekly periods."""

from solver.constraints.base import Constraint
from solver.types import SolverContext


class WeeklyPeriodsConstraint(Constraint):
    name = "weekly_periods"
    is_hard = True

    def apply(self, context: SolverContext) -> None:
        for (cid, subj), (weekly, _) in context.class_subject_info.items():
            context.model.Add(
                sum(
                    context.assign.get((cid, subj, d, p), 0)
                    for d in range(context.num_days)
                    for p in range(context.num_periods)
                    if p not in context.breaks
                )
                == weekly
            )
