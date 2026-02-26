# Timable Improvements

## Changes Made

### Math/Solver Fixes
- Fixed teacher limits bug in `types.py` - was using `max()` instead of `min()`
- Integrated scoring into `engine.py` - solver now optimizes for quality
- Connected priority configs to solver

### Data Handling
- New `database.py` - Full SQLite implementation with ACID, backups, migrations
- New `storage_v2.py` - Unified API with JSON fallback
- New `migrate.py` - Migration tool

### Models
- Fixed `ClassPriorityConfig` fields
- Added `sections` to Teacher model
