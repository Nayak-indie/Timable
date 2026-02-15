"""Hard constraint: max periods per day for each teacher (auto-relaxed)."""

from solver.constraints.base import Constraint
from solver.types import SolverContext


class TeacherDailyCapConstraint(Constraint):
    name = "teacher_daily_cap"
    is_hard = True

    def apply(self, context: SolverContext) -> None:
        for t in context.teachers:
            for d in range(context.num_days):
                vars_this_day = [
                    context.assign[(cid, subj, d, p)]
                    for (cid, subj), (_, tid) in context.class_subject_info.items()
                    if tid == t.teacher_id
                    for p in range(context.num_periods)
                    if p not in context.breaks
                ]
                if vars_this_day:
                    context.model.Add(
                        sum(vars_this_day)
                        <= context.effective_teacher_limits[t.teacher_id]
                    )
