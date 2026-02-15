"""Abstract base class for all constraints."""

from abc import ABC, abstractmethod

from solver.types import SolverContext


class Constraint(ABC):
    """Base class that every constraint module must inherit."""

    name: str
    is_hard: bool = True

    @abstractmethod
    def apply(self, context: SolverContext) -> None:
        """Add this constraint to the CP-SAT model via context."""
        ...
