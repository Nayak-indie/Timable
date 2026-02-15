"""Timetable solver package — public API."""

from solver.engine import invert_to_teacher_timetable, solve_timetable
from solver.improver import improve_timetable
from solver.rotation import generate_rotations

__all__ = [
    "solve_timetable",
    "invert_to_teacher_timetable",
    "improve_timetable",
    "generate_rotations",
]
