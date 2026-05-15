"""Hard constraint: avoid consecutive free periods for classes."""

from solver.constraints.base import Constraint
from solver.types import SolverContext


class ClassGapConstraint(Constraint):
    name = "class_gap_constraint"
    is_hard = False

    def apply(self, context: SolverContext) -> None:

        for cid in context.class_ids:

            for d in range(context.num_days):

                for p in range(context.num_periods - 1):

                    # Skip breaks
                    if p in context.breaks or (p + 1) in context.breaks:
                        continue

                    current_slot = []
                    next_slot = []

                    # Collect all assignments for current period
                    for (class_id, subj), _ in context.class_subject_info.items():

                        if class_id != cid:
                            continue

                        current_slot.append(
                            context.assign[(cid, subj, d, p)]
                        )

                        next_slot.append(
                            context.assign[(cid, subj, d, p + 1)]
                        )

                    # If BOTH periods are free → forbidden
                    #
                    # sum(current_slot) == 0  means no class assigned
                    # sum(next_slot) == 0 means no class assigned
                    #
                    # Together disallow consecutive free periods

                    current_has_class = context.model.NewBoolVar(
                        f"{cid}_{d}_{p}_has_class"
                    )

                    next_has_class = context.model.NewBoolVar(
                        f"{cid}_{d}_{p+1}_has_class"
                    )

                    context.model.Add(sum(current_slot) > 0).OnlyEnforceIf(
                        current_has_class
                    )

                    context.model.Add(sum(current_slot) == 0).OnlyEnforceIf(
                        current_has_class.Not()
                    )

                    context.model.Add(sum(next_slot) > 0).OnlyEnforceIf(
                        next_has_class
                    )

                    context.model.Add(sum(next_slot) == 0).OnlyEnforceIf(
                        next_has_class.Not()
                    )

                    # Prevent both from being free simultaneously
                    context.model.AddBoolOr([
                        current_has_class,
                        next_has_class
                    ])