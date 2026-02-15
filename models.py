
"""
models.py — Data models for Timable
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Teacher:
    id: str
    name: str
    subjects: List[str]
    max_periods_per_day: int = 6
    max_periods_per_week: int = 30

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
    subject_priority: Dict[str, int]  # subject -> priority (higher = more important)

@dataclass
class ScenarioState:
    last_timetable: Optional[dict] = None
    history: List[dict] = field(default_factory=list)
    priority_configs: List[ClassPriorityConfig] = field(default_factory=list)
    config: Optional[SchoolConfig] = None
