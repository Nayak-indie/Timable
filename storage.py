"""
🧠 STORAGE — File-based persistence
===================================
All data saved to disk. Refresh → everything still there.
"""
"""
storage.py — Data persistence for Timable
"""
import json
from pathlib import Path
from typing import List, Optional
from models import Teacher, Class, SchoolConfig, ClassPriorityConfig, ScenarioState, ClassSubject

DATA_DIR = Path(__file__).parent / "data"
TEACHERS_FILE = DATA_DIR / "teachers.json"
CLASSES_FILE = DATA_DIR / "classes.json"
CONFIG_FILE = DATA_DIR / "config.json"
PRIORITY_FILE = DATA_DIR / "priority_configs.json"
SCENARIO_FILE = DATA_DIR / "scenario_state.json"

def _ensure_data_dir() -> None:
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def save_teachers(teachers: List[Teacher]) -> None:
    """Save all teachers to disk. Overwrites existing file."""
    _ensure_data_dir()
    data = [_teacher_to_dict(t) for t in teachers]
    with open(TEACHERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_teachers() -> List[Teacher]:
    """Load all teachers from disk. Returns empty list if file doesn't exist."""
    _ensure_data_dir()
    if not TEACHERS_FILE.exists():
        return []
    try:
        with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [_dict_to_teacher(d) for d in data]
    except (json.JSONDecodeError, KeyError):
        return []

def save_classes(classes: List[Class]) -> None:
    """Save all classes to disk. Overwrites existing file."""
    _ensure_data_dir()
    data = [_class_to_dict(c) for c in classes]
    with open(CLASSES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_classes() -> List[Class]:
    """Load all classes from disk. Returns empty list if file doesn't exist."""
    _ensure_data_dir()
    if not CLASSES_FILE.exists():
        return []
    try:
        with open(CLASSES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [_dict_to_class(d) for d in data]
    except (json.JSONDecodeError, KeyError):
        return []

def save_config(config: SchoolConfig) -> None:
    """Save school config to disk."""
    _ensure_data_dir()
    data = {
        "days": config.days,
        "periods_per_day": config.periods_per_day,
        "break_periods": {str(k): v for k, v in config.break_periods.items()},
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_config() -> Optional[SchoolConfig]:
    """Load school config from disk."""
    _ensure_data_dir()
    if not CONFIG_FILE.exists():
        return SchoolConfig(
            days=["Mon", "Tue", "Wed", "Thu", "Fri"],
            periods_per_day=8,
            break_periods={3: "Lunch"},
        )
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        bp_raw = d.get("break_periods", {"3": "Lunch"})
        break_periods = {}
        for k, v in bp_raw.items():
            try:
                break_periods[int(k)] = str(v)
            except (ValueError, TypeError):
                pass
        return SchoolConfig(
            days=d.get("days", ["Mon", "Tue", "Wed", "Thu", "Fri"]),
            periods_per_day=d.get("periods_per_day", 8),
            break_periods=break_periods or {3: "Lunch"},
        )
    except (json.JSONDecodeError, KeyError):
        return SchoolConfig(days=["Mon", "Tue", "Wed", "Thu", "Fri"], periods_per_day=8, break_periods={3: "Lunch"})

def save_priority_configs(configs: List[ClassPriorityConfig]) -> None:
    """Save priority configs to disk."""
    _ensure_data_dir()
    data = [
        {
            "class_id": p.class_id,
            "priority_subjects": p.priority_subjects,
            "weak_subjects": p.weak_subjects,
            "heavy_subjects": p.heavy_subjects,
        }
        for p in configs
    ]
    with open(PRIORITY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_priority_configs() -> List[ClassPriorityConfig]:
    """Load priority configs from disk."""
    _ensure_data_dir()
    if not PRIORITY_FILE.exists():
        return []
    try:
        with open(PRIORITY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [
            ClassPriorityConfig(
                class_id=d["class_id"],
                priority_subjects=d.get("priority_subjects", []),
                weak_subjects=d.get("weak_subjects", []),
                heavy_subjects=d.get("heavy_subjects", []),
            )
            for d in data
        ]
    except (json.JSONDecodeError, KeyError):
        return []

def save_scenario_state(state: ScenarioState) -> None:
    """Save scenario state."""
    _ensure_data_dir()
    with open(SCENARIO_FILE, "w", encoding="utf-8") as f:
        json.dump({
            **state.__dict__,
            "priority_configs": [c.__dict__ for c in state.priority_configs],
            "config": state.config.__dict__ if state.config else None
        }, f, indent=2)

def load_scenario_state() -> Optional[ScenarioState]:
    """Load what-if scenario state."""
    _ensure_data_dir()
    if not SCENARIO_STATE_FILE.exists():
        return {"selected_day": 0, "scenarios": {}}
    try:
        with open(SCENARIO_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return {"selected_day": 0, "scenarios": {}}

import json
from pathlib import Path
from typing import List, Any, Optional
from datetime import datetime

from models import Teacher, Class, ClassSubject, ClassPriorityConfig, SchoolConfig


DATA_DIR = Path(__file__).parent / "data"
TEACHERS_FILE = DATA_DIR / "teachers.json"
CLASSES_FILE = DATA_DIR / "classes.json"
PRIORITY_FILE = DATA_DIR / "priority_configs.json"
CONFIG_FILE = DATA_DIR / "config.json"
HISTORY_FILE = DATA_DIR / "history.json"
DEMO_LOADED_FILE = DATA_DIR / "demo_loaded.json"
BASE_TIMETABLE_FILE = DATA_DIR / "base_timetable.json"
SCENARIO_STATE_FILE = DATA_DIR / "scenario_state.json"


def _ensure_data_dir() -> None:
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _teacher_to_dict(t: Teacher) -> dict:
    """Convert Teacher to JSON-serializable dict."""
    return {
        "teacher_id": t.teacher_id,
        "subjects": t.subjects,
        "sections": t.sections,
        "max_periods_per_day": t.max_periods_per_day,
    }


def _dict_to_teacher(d):
    # We only pull out the parts the Teacher class actually knows how to handle
    return Teacher(
        name=d.get("name", "Unknown"),
        subjects=d.get("subjects", []),
        sections=d.get("sections", []),
        max_periods_per_day=d.get("max_periods_per_day", 6)
    )


def _class_to_dict(c: Class) -> dict:
    """Convert Class to JSON-serializable dict."""
    return {
        "class_id": c.class_id,
        "subjects": [
            {"subject": cs.subject, "weekly_periods": cs.weekly_periods, "teacher_id": cs.teacher_id}
            for cs in c.subjects
        ],
    }


def _dict_to_class(d: dict) -> Class:
    """Convert dict from JSON back to Class."""
    subs = [
        ClassSubject(
            subject=s["subject"],
            weekly_periods=s["weekly_periods"],
            teacher_id=s["teacher_id"],
        )
        for s in d.get("subjects", [])
    ]
    return Class(class_id=d["class_id"], subjects=subs)


def load_teachers() -> List[Teacher]:
    """Load all teachers from disk. Returns empty list if file doesn't exist."""
    _ensure_data_dir()
    if not TEACHERS_FILE.exists():
        return []
    try:
        with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [_dict_to_teacher(d) for d in data]
    except (json.JSONDecodeError, KeyError):
        return []


def save_teachers(teachers: List[Teacher]) -> None:
    """Save all teachers to disk. Overwrites existing file."""
    _ensure_data_dir()
    data = [_teacher_to_dict(t) for t in teachers]
    with open(TEACHERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_classes() -> List[Class]:
    """Load all classes from disk. Returns empty list if file doesn't exist."""
    _ensure_data_dir()
    if not CLASSES_FILE.exists():
        return []
    try:
        with open(CLASSES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [_dict_to_class(d) for d in data]
    except (json.JSONDecodeError, KeyError):
        return []


def save_classes(classes: List[Class]) -> None:
    """Save all classes to disk. Overwrites existing file."""
    _ensure_data_dir()
    data = [_class_to_dict(c) for c in classes]
    with open(CLASSES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_priority_configs() -> List[ClassPriorityConfig]:
    """Load priority configs from disk."""
    _ensure_data_dir()
    if not PRIORITY_FILE.exists():
        return []
    try:
        with open(PRIORITY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [
            ClassPriorityConfig(
                class_id=d["class_id"],
                priority_subjects=d.get("priority_subjects", []),
                weak_subjects=d.get("weak_subjects", []),
                heavy_subjects=d.get("heavy_subjects", []),
            )
            for d in data
        ]
    except (json.JSONDecodeError, KeyError):
        return []


def save_priority_configs(configs: List[ClassPriorityConfig]) -> None:
    """Save priority configs to disk."""
    _ensure_data_dir()
    data = [
        {
            "class_id": p.class_id,
            "priority_subjects": p.priority_subjects,
            "weak_subjects": p.weak_subjects,
            "heavy_subjects": p.heavy_subjects,
        }
        for p in configs
    ]
    with open(PRIORITY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_config() -> SchoolConfig:
    """Load school config from disk."""
    _ensure_data_dir()
    if not CONFIG_FILE.exists():
        return SchoolConfig(
            days=["Mon", "Tue", "Wed", "Thu", "Fri"],
            periods_per_day=8,
            break_periods={3: "Lunch"},
        )
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        bp_raw = d.get("break_periods", {"3": "Lunch"})
        break_periods = {}
        for k, v in bp_raw.items():
            try:
                break_periods[int(k)] = str(v)
            except (ValueError, TypeError):
                pass
        return SchoolConfig(
            days=d.get("days", ["Mon", "Tue", "Wed", "Thu", "Fri"]),
            periods_per_day=d.get("periods_per_day", 8),
            break_periods=break_periods or {3: "Lunch"},
        )
    except (json.JSONDecodeError, KeyError):
        return SchoolConfig(days=["Mon", "Tue", "Wed", "Thu", "Fri"], periods_per_day=8, break_periods={3: "Lunch"})


def save_config(config: SchoolConfig) -> None:
    """Save school config to disk."""
    _ensure_data_dir()
    data = {
        "days": config.days,
        "periods_per_day": config.periods_per_day,
        "break_periods": {str(k): v for k, v in config.break_periods.items()},
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_history() -> List[dict]:
    """Load activity history. Newest first."""
    _ensure_data_dir()
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return []


def is_demo_loaded() -> bool:
    """Check if demo data has been loaded (button should be disabled)."""
    _ensure_data_dir()
    if not DEMO_LOADED_FILE.exists():
        return False
    try:
        with open(DEMO_LOADED_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("loaded", False)
    except (json.JSONDecodeError, KeyError):
        return False


def set_demo_loaded() -> None:
    """Mark demo data as loaded. Persists across refresh."""
    _ensure_data_dir()
    with open(DEMO_LOADED_FILE, "w", encoding="utf-8") as f:
        json.dump({"loaded": True}, f)


def clear_demo_loaded() -> None:
    """Reset demo flag (e.g. when user clears all data)."""
    if DEMO_LOADED_FILE.exists():
        DEMO_LOADED_FILE.unlink()


def load_base_timetable() -> Optional[dict]:
    """Load base timetable (serialized). Returns None if not found."""
    _ensure_data_dir()
    if not BASE_TIMETABLE_FILE.exists():
        return None
    try:
        with open(BASE_TIMETABLE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return None


def save_base_timetable(serialized: dict) -> None:
    """Save base timetable."""
    _ensure_data_dir()
    with open(BASE_TIMETABLE_FILE, "w", encoding="utf-8") as f:
        json.dump(serialized, f, indent=2)


def load_scenario_state() -> dict:
    """Load what-if scenario state."""
    _ensure_data_dir()
    if not SCENARIO_STATE_FILE.exists():
        return {"selected_day": 0, "scenarios": {}}
    try:
        with open(SCENARIO_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return {"selected_day": 0, "scenarios": {}}


def save_scenario_state(state: dict) -> None:
    """Save scenario state."""
    _ensure_data_dir()
    with open(SCENARIO_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def clear_base_timetable() -> None:
    """Remove base timetable file (e.g. when clearing all data)."""
    if BASE_TIMETABLE_FILE.exists():
        BASE_TIMETABLE_FILE.unlink()


def clear_scenario_state() -> None:
    """Remove scenario state file."""
    if SCENARIO_STATE_FILE.exists():
        SCENARIO_STATE_FILE.unlink()


def append_history(action: str, target: str, summary: str, details: str = "") -> None:
    """Append one history entry. Keeps last 500 entries."""
    _ensure_data_dir()
    history = load_history()
    entry = {
        "ts": datetime.now().isoformat(),
        "action": action,
        "target": target,
        "summary": summary,
        "details": details,
    }
    history.insert(0, entry)
    history = history[:500]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
