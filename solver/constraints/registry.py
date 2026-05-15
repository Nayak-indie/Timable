"""Constraint registration and management."""

from typing import Dict, List

from solver.constraints.base import Constraint

from .teacher_clash import TeacherClashConstraint
from .class_gap_constraint import ClassGapConstraint
from .class_free_periods import ClassFreePeriodsConstraint


class ConstraintRegistry:
    """Manages constraint registration and enables/disables them dynamically."""

    def __init__(self):
        self._constraints: Dict[str, Constraint] = {}
        self._enabled: Dict[str, bool] = {}

        # Register constraints here
        self.register(TeacherClashConstraint())
        self.register(ClassGapConstraint())
        self.register(ClassFreePeriodsConstraint())

    def register(self, constraint: Constraint) -> None:
        self._constraints[constraint.name] = constraint
        self._enabled[constraint.name] = True

    def enable(self, name: str) -> None:
        if name in self._constraints:
            self._enabled[name] = True

    def disable(self, name: str) -> None:
        if name in self._constraints:
            self._enabled[name] = False

    def is_enabled(self, name: str) -> bool:
        return self._enabled.get(name, False)

    def get_active(self) -> List[Constraint]:
        return [
            c for name, c in self._constraints.items()
            if self._enabled.get(name, False)
        ]

    def get_all(self) -> List[Constraint]:
        return list(self._constraints.values())

    def list_names(self) -> List[str]:
        return list(self._constraints.keys())