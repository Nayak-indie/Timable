
"""
models.py — Data models for Timable
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Teacher:
    teacher_id: str  # We use teacher_id to match your storage.py
    name: str
    subjects: List[str] = field(default_factory=list)
    sections: List[str] = field(default_factory=list)
    max_periods_per_day: int = 6
    max_periods_per_week: int = 30
    # Desired minimum number of free periods per day. This is a UX hint;
    # solver uses max_periods_per_day = periods_per_day - target_free_periods_per_day.
    target_free_periods_per_day: int = 0

@dataclass
class ClassSubject:
    subject: str
    weekly_periods: int
    teacher_id: str

@dataclass
class Class:
    id: str
    name: str
    subjects: List[ClassSubject]

@dataclass
class SchoolConfig:
    days: List[str] = field(default_factory=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri"])
    periods_per_day: int = 8
    break_periods: Dict[int, str] = field(default_factory=dict)  # e.g. {3: "Lunch"}

@dataclass
class ClassPriorityConfig:
    class_id: str
    priority_subjects: List[str] = field(default_factory=list)  # subjects to schedule early
    weak_subjects: List[str] = field(default_factory=list)  # subjects that can be bumped
    heavy_subjects: List[str] = field(default_factory=list)  # avoid back-to-back

@dataclass
class ScenarioState:
    last_timetable: Optional[dict] = None
    history: List[dict] = field(default_factory=list)
    priority_configs: List[ClassPriorityConfig] = field(default_factory=list)
    config: Optional[SchoolConfig] = None
