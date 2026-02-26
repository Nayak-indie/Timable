"""
Timable Database - Robust SQLite-based persistence with schema versioning.

Key features:
- ACID transactions (atomic writes)
- Schema versioning with migration support
- Relational queries (efficient lookups)
- Backup before writes
- Comprehensive error handling with logging
"""

import json
import logging
import os
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from models import (
    Class,
    ClassPriorityConfig,
    ClassSubject,
    SchoolConfig,
    Teacher,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATA_DIR = Path(__file__).parent / "data"
DB_FILE = DATA_DIR / "timetable.db"
SCHEMA_VERSION = "1.0.0"

# Backup configuration
MAX_BACKUPS = 5
BACKUP_DIR = DATA_DIR / "backups"


class TimableDB:
    """Main database class with schema versioning and atomic operations."""

    def __init__(self, db_path: Path = DB_FILE):
        self.db_path = db_path
        self._ensure_data_dir()
        self._init_connection()
        self._run_migrations()

    def _ensure_data_dir(self) -> None:
        """Create data and backup directories if they don't exist."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    def _init_connection(self) -> None:
        """Initialize database connection with proper settings."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        logger.info(f"Database connected: {self.db_path}")

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for atomic transactions."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Transaction failed: {e}")
            raise

    def _create_backup(self) -> Optional[Path]:
        """Create a timestamped backup before modifications."""
        if not self.db_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"timetable_{timestamp}.db"

        try:
            self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
            self._cleanup_old_backups()
            return backup_path
        except Exception as e:
            logger.warning(f"Backup failed: {e}")
            return None

    def _cleanup_old_backups(self) -> None:
        """Remove old backups exceeding MAX_BACKUPS."""
        try:
            backups = sorted(BACKUP_DIR.glob("timetable_*.db"), key=os.path.getmtime)
            for old_backup in backups[:-MAX_BACKUPS]:
                old_backup.unlink()
                logger.debug(f"Removed old backup: {old_backup}")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

    def _run_migrations(self) -> None:
        """Run schema migrations based on current version."""
        current_version = self._get_schema_version()

        if current_version is None:
            self._create_schema()
            self._set_schema_version(SCHEMA_VERSION)
            logger.info("Database schema created")
        elif current_version != SCHEMA_VERSION:
            self._migrate(current_version)
            logger.info(f"Migrated from {current_version} to {SCHEMA_VERSION}")

    def _get_schema_version(self) -> Optional[str]:
        """Get current schema version from database."""
        try:
            cursor = self.conn.execute(
                "SELECT value FROM meta WHERE key = 'schema_version'"
            )
            row = cursor.fetchone()
            return row["value"] if row else None
        except sqlite3.OperationalError:
            return None

    def _set_schema_version(self, version: str) -> None:
        """Set schema version in database."""
        self.conn.execute(
            "INSERT OR REPLACE INTO meta (key, value, updated_at) VALUES (?, ?, ?)",
            ("schema_version", version, datetime.now().isoformat()),
        )
        self.conn.commit()

    def _create_schema(self) -> None:
        """Create initial database schema."""
        # Use separate string to avoid any f-string issues
        default_days = '["Mon","Tue","Wed","Thu","Fri"]'
        default_breaks = '{"3":"Lunch"}'
        now = datetime.now().isoformat()
        
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                subjects TEXT NOT NULL,
                sections TEXT NOT NULL DEFAULT '[]',
                max_periods_per_day INTEGER NOT NULL DEFAULT 6,
                max_periods_per_week INTEGER NOT NULL DEFAULT 30,
                target_free_periods_per_day INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS classes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS class_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                weekly_periods INTEGER NOT NULL,
                teacher_id TEXT NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE RESTRICT,
                UNIQUE(class_id, subject)
            );

            CREATE INDEX IF NOT EXISTS idx_class_subjects_class ON class_subjects(class_id);
            CREATE INDEX IF NOT EXISTS idx_class_subjects_teacher ON class_subjects(teacher_id);

            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                days TEXT NOT NULL,
                periods_per_day INTEGER NOT NULL DEFAULT 8,
                break_periods TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS timetable (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id TEXT NOT NULL,
                day_index INTEGER NOT NULL,
                period_index INTEGER NOT NULL,
                subject TEXT NOT NULL,
                teacher_id TEXT NOT NULL,
                week_offset INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE RESTRICT,
                UNIQUE(class_id, day_index, period_index, week_offset)
            );

            CREATE INDEX IF NOT EXISTS idx_timetable_class ON timetable(class_id, week_offset);
            CREATE INDEX IF NOT EXISTS idx_timetable_teacher ON timetable(teacher_id, day_index, period_index);

            CREATE TABLE IF NOT EXISTS priority_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id TEXT NOT NULL UNIQUE,
                priority_subjects TEXT NOT NULL DEFAULT '[]',
                weak_subjects TEXT NOT NULL DEFAULT '[]',
                heavy_subjects TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                scenario_type TEXT NOT NULL,
                config TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                target TEXT NOT NULL,
                summary TEXT NOT NULL,
                details TEXT DEFAULT '',
                timestamp TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp DESC);
        """)
        
        # Insert default config using parameterized query
        self.conn.execute(
            "INSERT INTO config (id, days, periods_per_day, break_periods, updated_at) VALUES (1, ?, 8, ?, ?)",
            (default_days, default_breaks, now)
        )
        self.conn.commit()

    def _migrate(self, from_version: str) -> None:
        """Migrate schema from one version to another."""
        # Future migrations go here
        pass

    # -------------------------------------------------------------------------
    # Teacher operations
    # -------------------------------------------------------------------------

    def save_teacher(self, teacher: Teacher) -> None:
        """Insert or update a teacher."""
        now = datetime.now().isoformat()
        with self.transaction():
            self.conn.execute(
                """INSERT OR REPLACE INTO teachers
                   (teacher_id, name, subjects, sections, max_periods_per_day,
                    max_periods_per_week, target_free_periods_per_day, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM teachers WHERE teacher_id = ?), ?), ?)""",
                (
                    teacher.teacher_id,
                    teacher.name,
                    json.dumps(teacher.subjects),
                    json.dumps(getattr(teacher, "sections", [])),
                    teacher.max_periods_per_day,
                    teacher.max_periods_per_week,
                    getattr(teacher, "target_free_periods_per_day", 0),
                    teacher.teacher_id,
                    now,
                    now,
                ),
            )
        logger.info(f"Saved teacher: {teacher.teacher_id}")

    def save_teachers_batch(self, teachers: List[Teacher]) -> None:
        """Save multiple teachers in a single transaction."""
        self._create_backup()
        with self.transaction():
            now = datetime.now().isoformat()
            for teacher in teachers:
                self.conn.execute(
                    """INSERT OR REPLACE INTO teachers
                       (teacher_id, name, subjects, sections, max_periods_per_day,
                        max_periods_per_week, target_free_periods_per_day, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM teachers WHERE teacher_id = ?), ?), ?)""",
                    (
                        teacher.teacher_id,
                        teacher.name,
                        json.dumps(teacher.subjects),
                        json.dumps(getattr(teacher, "sections", [])),
                        teacher.max_periods_per_day,
                        teacher.max_periods_per_week,
                        getattr(teacher, "target_free_periods_per_day", 0),
                        teacher.teacher_id,
                        now,
                        now,
                    ),
                )
        logger.info(f"Saved {len(teachers)} teachers")

    def load_teachers(self) -> List[Teacher]:
        """Load all teachers from database."""
        cursor = self.conn.execute("SELECT * FROM teachers ORDER BY name")
        teachers = []
        for row in cursor:
            teachers.append(
                Teacher(
                    teacher_id=row["teacher_id"],
                    name=row["name"],
                    subjects=json.loads(row["subjects"]),
                    sections=json.loads(row["sections"]),
                    max_periods_per_day=row["max_periods_per_day"],
                    max_periods_per_week=row["max_periods_per_week"],
                    target_free_periods_per_day=row["target_free_periods_per_day"],
                )
            )
        return teachers

    def delete_teacher(self, teacher_id: str) -> bool:
        """Delete a teacher. Returns True if deleted."""
        cursor = self.conn.execute(
            "DELETE FROM teachers WHERE teacher_id = ?", (teacher_id,)
        )
        self.conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted teacher: {teacher_id}")
        return deleted

    def get_teacher_by_id(self, teacher_id: str) -> Optional[Teacher]:
        """Get a single teacher by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM teachers WHERE teacher_id = ?", (teacher_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Teacher(
            teacher_id=row["teacher_id"],
            name=row["name"],
            subjects=json.loads(row["subjects"]),
            sections=json.loads(row["sections"]),
            max_periods_per_day=row["max_periods_per_day"],
            max_periods_per_week=row["max_periods_per_week"],
            target_free_periods_per_day=row["target_free_periods_per_day"],
        )

    # -------------------------------------------------------------------------
    # Class operations
    # -------------------------------------------------------------------------

    def save_class(self, class_obj: Class) -> None:
        """Insert or update a class and its subjects."""
        now = datetime.now().isoformat()
        with self.transaction():
            self.conn.execute(
                """INSERT OR REPLACE INTO classes (id, name, created_at, updated_at)
                   VALUES (?, ?, COALESCE((SELECT created_at FROM classes WHERE id = ?), ?), ?)""",
                (class_obj.id, getattr(class_obj, "name", class_obj.id), class_obj.id, now, now),
            )

            self.conn.execute("DELETE FROM class_subjects WHERE class_id = ?", (class_obj.id,))

            for cs in class_obj.subjects:
                self.conn.execute(
                    """INSERT INTO class_subjects (class_id, subject, weekly_periods, teacher_id)
                       VALUES (?, ?, ?, ?)""",
                    (class_obj.id, cs.subject, cs.weekly_periods, cs.teacher_id),
                )
        logger.info(f"Saved class: {class_obj.id}")

    def save_classes_batch(self, classes: List[Class]) -> None:
        """Save multiple classes in a single transaction."""
        self._create_backup()
        with self.transaction():
            now = datetime.now().isoformat()
            for class_obj in classes:
                self.conn.execute(
                    """INSERT OR REPLACE INTO classes (id, name, created_at, updated_at)
                       VALUES (?, ?, COALESCE((SELECT created_at FROM classes WHERE id = ?), ?), ?)""",
                    (class_obj.id, getattr(class_obj, "name", class_obj.id), class_obj.id, now, now),
                )
                self.conn.execute("DELETE FROM class_subjects WHERE class_id = ?", (class_obj.id,))
                for cs in class_obj.subjects:
                    self.conn.execute(
                        "INSERT INTO class_subjects (class_id, subject, weekly_periods, teacher_id) VALUES (?, ?, ?, ?)",
                        (class_obj.id, cs.subject, cs.weekly_periods, cs.teacher_id),
                    )
        logger.info(f"Saved {len(classes)} classes")

    def load_classes(self) -> List[Class]:
        """Load all classes with their subjects."""
        cursor = self.conn.execute("SELECT * FROM classes ORDER BY id")
        classes = []
        for row in cursor:
            subj_cursor = self.conn.execute(
                "SELECT subject, weekly_periods, teacher_id FROM class_subjects WHERE class_id = ?",
                (row["id"],),
            )
            subjects = [
                ClassSubject(
                    subject=sr["subject"],
                    weekly_periods=sr["weekly_periods"],
                    teacher_id=sr["teacher_id"],
                )
                for sr in subj_cursor
            ]
            classes.append(
                Class(id=row["id"], name=row["name"], subjects=subjects)
            )
        return classes

    def delete_class(self, class_id: str) -> bool:
        """Delete a class. Returns True if deleted."""
        cursor = self.conn.execute("DELETE FROM classes WHERE id = ?", (class_id,))
        self.conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted class: {class_id}")
        return deleted

    def get_classes_by_teacher(self, teacher_id: str) -> List[Class]:
        """Get all classes taught by a specific teacher."""
        cursor = self.conn.execute(
            """SELECT DISTINCT c.id, c.name FROM classes c
               JOIN class_subjects cs ON c.id = cs.class_id
               WHERE cs.teacher_id = ?""",
            (teacher_id,),
        )
        classes = []
        for row in cursor:
            subj_cursor = self.conn.execute(
                "SELECT subject, weekly_periods, teacher_id FROM class_subjects WHERE class_id = ?",
                (row["id"],),
            )
            subjects = [
                ClassSubject(
                    subject=sr["subject"],
                    weekly_periods=sr["weekly_periods"],
                    teacher_id=sr["teacher_id"],
                )
                for sr in subj_cursor
            ]
            classes.append(Class(id=row["id"], name=row["name"], subjects=subjects))
        return classes

    # -------------------------------------------------------------------------
    # Config operations
    # -------------------------------------------------------------------------

    def load_config(self) -> SchoolConfig:
        """Load school configuration."""
        cursor = self.conn.execute("SELECT * FROM config WHERE id = 1")
        row = cursor.fetchone()
        if not row:
            return SchoolConfig()

        break_periods = {}
        bp_raw = json.loads(row["break_periods"])
        for k, v in bp_raw.items():
            try:
                break_periods[int(k)] = str(v)
            except (ValueError, TypeError):
                pass

        return SchoolConfig(
            days=json.loads(row["days"]),
            periods_per_day=row["periods_per_day"],
            break_periods=break_periods,
        )

    def save_config(self, config: SchoolConfig) -> None:
        """Save school configuration."""
        now = datetime.now().isoformat()
        with self.transaction():
            self.conn.execute(
                """INSERT OR REPLACE INTO config (id, days, periods_per_day, break_periods, updated_at)
                   VALUES (1, ?, ?, ?, ?)""",
                (
                    json.dumps(config.days),
                    config.periods_per_day,
                    json.dumps({str(k): v for k, v in config.break_periods.items()}),
                    now,
                ),
            )
        logger.info("Saved config")

    # -------------------------------------------------------------------------
    # Timetable operations
    # -------------------------------------------------------------------------

    def save_timetable(
        self,
        timetable: Dict[Tuple[str, int, int], Tuple[str, str]],
        week_offset: int = 0,
    ) -> None:
        """Save class timetable."""
        self._create_backup()
        with self.transaction():
            self.conn.execute(
                "DELETE FROM timetable WHERE week_offset = ?", (week_offset,)
            )

            now = datetime.now().isoformat()
            for (cid, day, period), (subj, tid) in timetable.items():
                self.conn.execute(
                    """INSERT INTO timetable (class_id, day_index, period_index, subject, teacher_id, week_offset, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (cid, day, period, subj, tid, week_offset, now),
                )
        logger.info(f"Saved timetable (week {week_offset})")

    def load_timetable(self, week_offset: int = 0) -> Dict[Tuple[str, int, int], Tuple[str, str]]:
        """Load class timetable."""
        cursor = self.conn.execute(
            "SELECT * FROM timetable WHERE week_offset = ?",
            (week_offset,),
        )
        result = {}
        for row in cursor:
            result[
                (row["class_id"], row["day_index"], row["period_index"])
            ] = (row["subject"], row["teacher_id"])
        return result

    def get_teacher_timetable(
        self, teacher_id: str
    ) -> Dict[Tuple[int, int], Tuple[str, str]]:
        """Get timetable for a specific teacher."""
        cursor = self.conn.execute(
            "SELECT day_index, period_index, class_id, subject FROM timetable WHERE teacher_id = ?",
            (teacher_id,),
        )
        return {
            (row["day_index"], row["period_index"]): (row["class_id"], row["subject"])
            for row in cursor
        }

    def get_free_teachers(self, day: int, period: int) -> List[Teacher]:
        """Get all teachers NOT teaching at a specific day/period."""
        cursor = self.conn.execute(
            """SELECT t.* FROM teachers t
               WHERE t.teacher_id NOT IN (
                   SELECT teacher_id FROM timetable
                   WHERE day_index = ? AND period_index = ?
               )""",
            (day, period),
        )
        return [
            Teacher(
                teacher_id=row["teacher_id"],
                name=row["name"],
                subjects=json.loads(row["subjects"]),
                max_periods_per_day=row["max_periods_per_day"],
                max_periods_per_week=row["max_periods_per_week"],
            )
            for row in cursor
        ]

    # -------------------------------------------------------------------------
    # Priority config operations
    # -------------------------------------------------------------------------

    def save_priority_config(self, config: ClassPriorityConfig) -> None:
        """Save class priority configuration."""
        now = datetime.now().isoformat()
        with self.transaction():
            self.conn.execute(
                """INSERT OR REPLACE INTO priority_configs
                   (class_id, priority_subjects, weak_subjects, heavy_subjects, created_at, updated_at)
                   VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM priority_configs WHERE class_id = ?), ?), ?)""",
                (
                    config.class_id,
                    json.dumps(getattr(config, "priority_subjects", [])),
                    json.dumps(getattr(config, "weak_subjects", [])),
                    json.dumps(getattr(config, "heavy_subjects", [])),
                    config.class_id,
                    now,
                    now,
                ),
            )

    def load_priority_configs(self) -> List[ClassPriorityConfig]:
        """Load all priority configurations."""
        cursor = self.conn.execute("SELECT * FROM priority_configs")
        configs = []
        for row in cursor:
            configs.append(
                ClassPriorityConfig(
                    class_id=row["class_id"],
                    priority_subjects=json.loads(row["priority_subjects"]),
                    weak_subjects=json.loads(row["weak_subjects"]),
                    heavy_subjects=json.loads(row["heavy_subjects"]),
                )
            )
        return configs

    # -------------------------------------------------------------------------
    # History operations
    # -------------------------------------------------------------------------

    def append_history(
        self, action: str, target: str, summary: str, details: str = ""
    ) -> None:
        """Add a history entry."""
        with self.transaction():
            self.conn.execute(
                """INSERT INTO history (action, target, summary, details, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (action, target, summary, details, datetime.now().isoformat()),
            )
        self.conn.execute(
            """DELETE FROM history WHERE id NOT IN
               (SELECT id FROM history ORDER BY timestamp DESC LIMIT 500)"""
        )
        self.conn.commit()

    def load_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Load recent history entries."""
        cursor = self.conn.execute(
            "SELECT * FROM history ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor]

    # -------------------------------------------------------------------------
    # Utility operations
    # -------------------------------------------------------------------------

    def clear_all(self) -> None:
        """Clear all data (for testing/reset)."""
        self._create_backup()
        with self.transaction():
            self.conn.execute("DELETE FROM timetable")
            self.conn.execute("DELETE FROM class_subjects")
            self.conn.execute("DELETE FROM classes")
            self.conn.execute("DELETE FROM teachers")
            self.conn.execute("DELETE FROM priority_configs")
            self.conn.execute("DELETE FROM scenarios")
            self.conn.execute("DELETE FROM history")
        logger.warning("All data cleared")

    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        stats = {}
        tables = ["teachers", "classes", "class_subjects", "timetable", "history"]
        for table in tables:
            cursor = self.conn.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            stats[table] = cursor.fetchone()["cnt"]
        return stats

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self, "conn"):
            self.conn.close()
            logger.info("Database connection closed")


# Global database instance
_db_instance: Optional[TimableDB] = None


def get_db() -> TimableDB:
    """Get or create global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = TimableDB()
    return _db_instance


def reset_db() -> None:
    """Reset global database instance (for testing)."""
    global _db_instance
    if _db_instance:
        _db_instance.close()
    _db_instance = None
