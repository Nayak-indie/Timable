"""Default constraint registration."""

from solver.constraints.class_clash import ClassClashConstraint
from solver.constraints.registry import ConstraintRegistry
from solver.constraints.teacher_clash import TeacherClashConstraint
from solver.constraints.teacher_daily_cap import TeacherDailyCapConstraint
from solver.constraints.weekly_periods import WeeklyPeriodsConstraint


def create_default_registry() -> ConstraintRegistry:
    """Create a registry with all built-in constraints enabled."""
    registry = ConstraintRegistry()
    registry.register(WeeklyPeriodsConstraint())
    registry.register(ClassClashConstraint())
    registry.register(TeacherClashConstraint())
    registry.register(TeacherDailyCapConstraint())
    return registry
