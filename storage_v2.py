"""
Storage abstraction layer - supports both legacy JSON and new SQLite backends.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from models import Class, ClassPriorityConfig, SchoolConfig, Teacher

logger = logging.getLogger(__name__)

USE_SQLITE_BY_DEFAULT = True
DATA_DIR = Path(__file__).parent / "data"

TEACHERS_FILE = DATA_DIR / "teachers.json"
CLASSES_FILE = DATA_DIR / "classes.json"
CONFIG_FILE = DATA_DIR / "config.json"

_db = None


def _get_db():
    global _db
    if _db is None:
        from database import get_db as _get_db
        _db = _get_db()
    return _db


# Teacher operations
def get_teachers() -> List[Teacher]:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        return _get_db().load_teachers()
    return _load_teachers_json()


def save_teachers(teachers: List[Teacher]) -> None:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        _get_db().save_teachers_batch(teachers)
    else:
        _save_teachers_json(teachers)


def get_teacher(teacher_id: str) -> Optional[Teacher]:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        return _get_db().get_teacher_by_id(teacher_id)
    teachers = _load_teachers_json()
    for t in teachers:
        if t.teacher_id == teacher_id:
            return t
    return None


def delete_teacher(teacher_id: str) -> bool:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        return _get_db().delete_teacher(teacher_id)
    teachers = _load_teachers_json()
    for i, t in enumerate(teachers):
        if t.teacher_id == teacher_id:
            teachers.pop(i)
            _save_teachers_json(teachers)
            return True
    return False


# Class operations
def get_classes() -> List[Class]:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        return _get_db().load_classes()
    return _load_classes_json()


def save_classes(classes: List[Class]) -> None:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        _get_db().save_classes_batch(classes)
    else:
        _save_classes_json(classes)


def get_class(class_id: str) -> Optional[Class]:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        classes = _get_db().load_classes()
        for c in classes:
            if c.id == class_id:
                return c
        return None
    classes = _load_classes_json()
    for c in classes:
        if c.id == class_id:
            return c
    return None


def delete_class(class_id: str) -> bool:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        return _get_db().delete_class(class_id)
    classes = _load_classes_json()
    for i, c in enumerate(classes):
        if c.id == class_id:
            classes.pop(i)
            _save_classes_json(classes)
            return True
    return False


def get_classes_by_teacher(teacher_id: str) -> List[Class]:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        return _get_db().get_classes_by_teacher(teacher_id)
    classes = _load_classes_json()
    return [c for c in classes if any(cs.teacher_id == teacher_id for cs in c.subjects)]


# Config operations
def get_config() -> SchoolConfig:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        return _get_db().load_config()
    return _load_config_json()


def save_config(config: SchoolConfig) -> None:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        _get_db().save_config(config)
    else:
        _save_config_json(config)


# Timetable operations
def get_timetable(week_offset: int = 0) -> dict:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        return _get_db().load_timetable(week_offset)
    return _load_timetable_json(week_offset)


def save_timetable(timetable: dict, week_offset: int = 0) -> None:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        _get_db().save_timetable(timetable, week_offset)
    else:
        _save_timetable_json(timetable, week_offset)


def get_teacher_timetable(teacher_id: str) -> dict:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        return _get_db().get_teacher_timetable(teacher_id)
    tt = get_timetable()
    return {(d, p): (cid, subj) for (cid, d, p), (subj, tid) in tt.items() if tid == teacher_id}


def get_free_teachers(day: int, period: int) -> List[Teacher]:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        return _get_db().get_free_teachers(day, period)
    tt = get_timetable()
    busy = {tid for (_, d, p), (subj, tid) in tt.items() if d == day and p == period}
    return [t for t in get_teachers() if t.teacher_id not in busy]


# Priority config operations
def get_priority_configs() -> List[ClassPriorityConfig]:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        return _get_db().load_priority_configs()
    return _load_priority_configs_json()


def save_priority_configs(configs: List[ClassPriorityConfig]) -> None:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        for config in configs:
            _get_db().save_priority_config(config)
    else:
        _save_priority_configs_json(configs)


# History operations
def append_history(action: str, target: str, summary: str, details: str = "") -> None:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        _get_db().append_history(action, target, summary, details)
    else:
        _append_history_json(action, target, summary, details)


def get_history(limit: int = 100) -> List[dict]:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        return _get_db().load_history(limit)
    return _load_history_json(limit)


# Utility functions
def clear_all() -> None:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        _get_db().clear_all()
    else:
        _clear_all_json()


def get_stats() -> dict:
    if USE_SQLITE_BY_DEFAULT and (DATA_DIR / "timetable.db").exists():
        return _get_db().get_stats()
    return _get_json_stats()


# Legacy JSON implementations
def _load_teachers_json() -> List[Teacher]:
    if not TEACHERS_FILE.exists():
        return []
    try:
        with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [_dict_to_teacher(d) for d in data]
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to load teachers: {e}")
        return []


def _save_teachers_json(teachers: List[Teacher]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = [_teacher_to_dict(t) for t in teachers]
    with open(TEACHERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _dict_to_teacher(d: dict) -> Teacher:
    return Teacher(
        teacher_id=d.get("teacher_id", d.get("name", "Unknown")),
        name=d.get("name", d.get("teacher_id", "Unknown")),
        subjects=d.get("subjects", []),
        sections=d.get("sections", []),
        max_periods_per_day=d.get("max_periods_per_day", 6),
        max_periods_per_week=d.get("max_periods_per_week", 30),
        target_free_periods_per_day=d.get("target_free_periods_per_day", 0),
    )


def _teacher_to_dict(t: Teacher) -> dict:
    return {
        "teacher_id": t.teacher_id,
        "name": t.name,
        "subjects": t.subjects,
        "sections": getattr(t, "sections", []),
        "max_periods_per_day": t.max_periods_per_day,
        "max_periods_per_week": getattr(t, "max_periods_per_week", 30),
        "target_free_periods_per_day": getattr(t, "target_free_periods_per_day", 0),
    }


def _load_classes_json() -> List[Class]:
    if not CLASSES_FILE.exists():
        return []
    try:
        with open(CLASSES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [_dict_to_class(d) for d in data]
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to load classes: {e}")
        return []


def _save_classes_json(classes: List[Class]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = [_class_to_dict(c) for c in classes]
    with open(CLASSES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _dict_to_class(d: dict) -> Class:
    from models import ClassSubject
    subs = [ClassSubject(subject=s["subject"], weekly_periods=s["weekly_periods"], teacher_id=s["teacher_id"]) for s in d.get("subjects", [])]
    return Class(id=d.get("id", d.get("class_id", "Unknown")), name=d.get("name", d.get("id", "Unknown")), subjects=subs)


def _class_to_dict(c: Class) -> dict:
    return {"id": c.id, "name": getattr(c, "name", c.id), "subjects": [{"subject": cs.subject, "weekly_periods": cs.weekly_periods, "teacher_id": cs.teacher_id} for cs in c.subjects]}


def _load_config_json() -> SchoolConfig:
    if not CONFIG_FILE.exists():
        return SchoolConfig()
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
        return SchoolConfig(days=d.get("days", ["Mon", "Tue", "Wed", "Thu", "Fri"]), periods_per_day=d.get("periods_per_day", 8), break_periods=break_periods or {3: "Lunch"})
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to load config: {e}")
        return SchoolConfig()


def _save_config_json(config: SchoolConfig) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {"days": config.days, "periods_per_day": config.periods_per_day, "break_periods": {str(k): v for k, v in config.break_periods.items()}}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _load_timetable_json(week_offset: int = 0) -> dict:
    base_file = DATA_DIR / "base_timetable.json"
    if not base_file.exists():
        return {}
    try:
        with open(base_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        result = {}
        for k, v in raw.items():
            try:
                cid, d_s, p_s = k.split("|")
                result[(cid, int(d_s), int(p_s))] = (v[0], v[1])
            except Exception:
                continue
        return result
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to load timetable: {e}")
        return {}


def _save_timetable_json(timetable: dict, week_offset: int = 0) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw = {f"{cid}|{d}|{p}": [subj, tid] for (cid, d, p), (subj, tid) in timetable.items()}
    with open(DATA_DIR / "base_timetable.json", "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2)


def _load_priority_configs_json() -> List[ClassPriorityConfig]:
    priority_file = DATA_DIR / "priority_configs.json"
    if not priority_file.exists():
        return []
    try:
        with open(priority_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [ClassPriorityConfig(class_id=d["class_id"], priority_subjects=d.get("priority_subjects", []), weak_subjects=d.get("weak_subjects", []), heavy_subjects=d.get("heavy_subjects", [])) for d in data]
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to load priority configs: {e}")
        return []


def _save_priority_configs_json(configs: List[ClassPriorityConfig]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = [{"class_id": p.class_id, "priority_subjects": p.priority_subjects, "weak_subjects": p.weak_subjects, "heavy_subjects": p.heavy_subjects} for p in configs]
    with open(DATA_DIR / "priority_configs.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _load_history_json(limit: int = 100) -> List[dict]:
    history_file = DATA_DIR / "history.json"
    if not history_file.exists():
        return []
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)[:limit]
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to load history: {e}")
        return []


def _append_history_json(action: str, target: str, summary: str, details: str = "") -> None:
    from datetime import datetime
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    history = _load_history_json(500)
    entry = {"ts": datetime.now().isoformat(), "action": action, "target": target, "summary": summary, "details": details}
    history.insert(0, entry)
    history = history[:500]
    with open(DATA_DIR / "history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def _clear_all_json() -> None:
    for f in [TEACHERS_FILE, CLASSES_FILE, CONFIG_FILE, DATA_DIR / "base_timetable.json", DATA_DIR / "priority_configs.json", DATA_DIR / "history.json", DATA_DIR / "demo_loaded.json", DATA_DIR / "scenario_state.json"]:
        if f.exists():
            f.unlink()


def _get_json_stats() -> dict:
    stats = {}
    for name, f in [("teachers", TEACHERS_FILE), ("classes", CLASSES_FILE)]:
        if f.exists():
            try:
                with open(f) as fp:
                    stats[name] = len(json.load(fp))
            except:
                stats[name] = 0
        else:
            stats[name] = 0
    return stats


# Aliases
load_teachers = get_teachers
save_teachers = save_teachers
load_classes = get_classes
save_classes = save_classes
load_config = get_config
save_config = save_config
load_history = get_history
append_history = append_history


def init_storage():
    global _db
    if USE_SQLITE_BY_DEFAULT:
        if not (DATA_DIR / "timetable.db").exists():
            if TEACHERS_FILE.exists() or CLASSES_FILE.exists():
                logger.info("Found existing JSON data, will use JSON fallback")
            else:
                _db = _get_db()
                logger.info("Created new SQLite database")
        else:
            _db = _get_db()
