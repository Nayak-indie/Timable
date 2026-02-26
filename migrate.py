#!/usr/bin/env python3
"""
Migration script - Convert existing JSON data to SQLite database.

Usage:
    python migrate.py          # Dry run (show what would be migrated)
    python migrate.py --force  # Actually perform migration
    python migrate.py --stats  # Show current storage stats
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import TimableDB
from storage_v2 import (
    DATA_DIR,
    TEACHERS_FILE,
    CLASSES_FILE,
    CONFIG_FILE,
    _load_teachers_json,
    _load_classes_json,
    _load_config_json,
    _load_timetable_json,
    _load_priority_configs_json,
)


def show_stats():
    """Show current storage statistics."""
    print("=" * 50)
    print("Storage Statistics")
    print("=" * 50)

    # JSON files
    print("\n📁 JSON Files:")
    for f in [TEACHERS_FILE, CLASSES_FILE, CONFIG_FILE]:
        if f.exists():
            size = f.stat().st_size
            print(f"  {f.name}: {size:,} bytes")
        else:
            print(f"  {f.name}: (not found)")

    db_file = DATA_DIR / "timetable.db"
    if db_file.exists():
        print(f"\n🗄️  SQLite Database:")
        print(f"  timetable.db: {db_file.stat().st_size:,} bytes")

        # Show table counts
        db = TimableDB()
        stats = db.get_stats()
        print("\n📊 Table Counts:")
        for table, count in stats.items():
            print(f"  {table}: {count}")
        db.close()
    else:
        print("\n🗄️  SQLite Database: (not found)")


def migrate(dry_run: bool = True):
    """Migrate JSON data to SQLite."""
    print("=" * 50)
    print("JSON → SQLite Migration")
    print("=" * 50)

    # Check if migration needed
    db_file = DATA_DIR / "timetable.db"
    if db_file.exists():
        print("\n⚠️  SQLite database already exists!")
        print("   Delete it manually if you want to re-migrate.")
        return False

    # Load JSON data
    print("\n📥 Loading JSON data...")
    teachers = _load_teachers_json()
    classes = _load_classes_json()
    config = _load_config_json()
    timetable = _load_timetable_json()
    priority_configs = _load_priority_configs_json()

    print(f"  Teachers: {len(teachers)}")
    print(f"  Classes: {len(classes)}")
    print(f"  Config: {config.days} days, {config.periods_per_day} periods")
    print(f"  Timetable entries: {len(timetable)}")
    print(f"  Priority configs: {len(priority_configs)}")

    if dry_run:
        print("\n🔍 Dry run complete. Run with --force to actually migrate.")
        return True

    # Perform migration
    print("\n💾 Creating SQLite database...")
    db = TimableDB()

    print("  Migrating teachers...")
    if teachers:
        db.save_teachers_batch(teachers)

    print("  Migrating classes...")
    if classes:
        db.save_classes_batch(classes)

    print("  Migrating config...")
    db.save_config(config)

    print("  Migrating timetable...")
    if timetable:
        db.save_timetable(timetable)

    print("  Migrating priority configs...")
    for pc in priority_configs:
        db.save_priority_config(pc)

    db.close()

    print("\n✅ Migration complete!")
    print(f"   Database: {db_file}")

    # Show final stats
    show_stats()

    return True


def rollback():
    """Rollback migration by deleting SQLite database."""
    db_file = DATA_DIR / "timetable.db"
    if db_file.exists():
        print(f"Deleting {db_file}...")
        db_file.unlink()
        print("✅ Rollback complete.")
    else:
        print("No SQLite database found.")


def main():
    parser = argparse.ArgumentParser(description="Timable Migration Tool")
    parser.add_argument("--stats", action="store_true", help="Show storage statistics")
    parser.add_argument("--migrate", action="store_true", help="Run migration")
    parser.add_argument("--force", action="store_true", help="Force migration (no dry run)")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.rollback:
        rollback()
    elif args.migrate:
        migrate(dry_run=not args.force)
    else:
        # Default: show stats
        show_stats()
        print("\n💡 Use --migrate to convert JSON to SQLite")
        print("💡 Use --migrate --force to do it for real")
        print("💡 Use --stats to see current state")


if __name__ == "__main__":
    main()
