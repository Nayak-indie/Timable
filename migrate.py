#!/usr/bin/env python3
"""Migration script - Convert JSON data to SQLite."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database import TimableDB
from storage_v2 import (
    DATA_DIR, TEACHERS_FILE, CLASSES_FILE, CONFIG_FILE,
    _load_teachers_json, _load_classes_json, _load_config_json,
    _load_timetable_json, _load_priority_configs_json,
)


def show_stats():
    print("=" * 50)
    print("Storage Statistics")
    print("=" * 50)
    print("\n📁 JSON Files:")
    for f in [TEACHERS_FILE, CLASSES_FILE, CONFIG_FILE]:
        if f.exists():
            print(f"  {f.name}: {f.stat().st_size:,} bytes")
        else:
            print(f"  {f.name}: (not found)")
    db_file = DATA_DIR / "timetable.db"
    if db_file.exists():
        print(f"\n🗄️  SQLite Database: {db_file.stat().st_size:,} bytes")
        db = TimableDB()
        stats = db.get_stats()
        print("\n📊 Table Counts:")
        for table, count in stats.items():
            print(f"  {table}: {count}")
        db.close()
    else:
        print("\n🗄️  SQLite Database: (not found)")


def migrate(dry_run=True):
    print("=" * 50)
    print("JSON → SQLite Migration")
    print("=" * 50)
    db_file = DATA_DIR / "timetable.db"
    if db_file.exists():
        print("\n⚠️  SQLite already exists!")
        return False
    print("\n📥 Loading JSON data...")
    teachers = _load_teachers_json()
    classes = _load_classes_json()
    config = _load_config_json()
    timetable = _load_timetable_json()
    priority_configs = _load_priority_configs_json()
    print(f"  Teachers: {len(teachers)}")
    print(f"  Classes: {len(classes)}")
    print(f"  Timetable entries: {len(timetable)}")
    if dry_run:
        print("\n🔍 Dry run. Run with --force to migrate.")
        return True
    print("\n💾 Creating SQLite database...")
    db = TimableDB()
    if teachers:
        db.save_teachers_batch(teachers)
    if classes:
        db.save_classes_batch(classes)
    db.save_config(config)
    if timetable:
        db.save_timetable(timetable)
    for pc in priority_configs:
        db.save_priority_config(pc)
    db.close()
    print("\n✅ Migration complete!")
    show_stats()
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", action="store_true", help="Show stats")
    parser.add_argument("--migrate", action="store_true", help="Run migration")
    parser.add_argument("--force", action="store_true", help="Force migration")
    args = parser.parse_args()
    if args.stats:
        show_stats()
    elif args.migrate:
        migrate(dry_run=not args.force)
    else:
        show_stats()
        print("\n💡 Use --migrate to convert JSON to SQLite")


if __name__ == "__main__":
    main()
