"""Soft-preferred rule: prefer at most 2 free periods/day per class.

This constraint no longer aborts the solve when violated. Instead it creates
penalty variables representing the number of free periods beyond 2 for each
class/day and registers them into the solver context's `soft_penalties` so
the objective can minimize these violations when optimizing.
"""

from solver.constraints.base import Constraint
from solver.types import SolverContext
from ortools.sat.python import cp_model


class ClassFreePeriodsConstraint(Constraint):
    name = "class_free_periods"
    is_hard = False

    def apply(self, context: SolverContext) -> None:
        model = context.model
        # available non-break slots per day
        available = context.num_periods - len(context.breaks)
        max_free = 2

        for cid in context.class_ids:
            for d in range(context.num_days):
                vars_for_day = []
                for (c, subj) in context.class_subject_info:
                    if c != cid:
                        continue
                    for p in range(context.num_periods):
                        if p in context.breaks:
                            continue
                        vars_for_day.append(context.assign[(cid, subj, d, p)])

                if not vars_for_day:
                    continue

                # free_count = available - sum(vars_for_day)
                free_count = model.NewIntVar(0, available, f"freecount_{cid}_{d}")
                model.Add(free_count == available - sum(vars_for_day))

                # penalty = max(0, free_count - max_free)
                penalty = model.NewIntVar(0, available, f"freepen_{cid}_{d}")
                # penalty >= free_count - max_free
                model.Add(penalty >= free_count - max_free)
                # penalty <= available (implicit by var domain)

                # Register penalty with configurable weight from SchoolConfig
                weight = context.config.penalty_weights.get(self.name, 10)
                context.soft_penalties.append((penalty, weight))
