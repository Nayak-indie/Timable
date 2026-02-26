"""
activity_logger.py - Records all user activities with timestamps
"""
import os
from datetime import datetime
from pathlib import Path
import pytz

# Log file path
LOG_FILE = Path(__file__).parent / "data" / "activity_log.txt"

def _ensure_log_dir():
    """Create log directory if it doesn't exist."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def _get_ist_time():
    """Get current time in IST."""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist)

def log_activity(action: str, details: str, category: str = "general"):
    """
    Log an activity to the text file.
    
    Args:
        action: Brief action description (e.g., "ADDED_TEACHER", "GENERATED_TIMETABLE")
        details: More details about the action
        category: Category of activity (teacher, class, timetable, system)
    """
    _ensure_log_dir()
    
    now = _get_ist_time()
    timestamp = now.strftime("%Y-%m-%d %I:%M %p IST")
    date_only = now.strftime("%Y-%m-%d")
    time_only = now.strftime("%I:%M %p")
    
    # Format for easy reading
    log_entry = f"[{timestamp}] {action}: {details}\n"
    
    # Also create a formatted line for the readable format
    formatted_entry = f"""
╔══════════════════════════════════════════════════════════════╗
║  ACTIVITY LOG - {date_only}                                   ║
╠══════════════════════════════════════════════════════════════╣
║  Time:    {time_only} (IST)                                ║
║  Action:  {action:<50} ║
║  Details: {details:<50} ║
║  Category: {category:<50} ║
╚══════════════════════════════════════════════════════════════╝
"""
    
    # Append to log file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted_entry)

def read_logs(last_n: int = 10) -> str:
    """Read the last N log entries."""
    if not LOG_FILE.exists():
        return "No activity logs found."
    
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    if not content:
        return "No activity logs found."
    
    # Return last N entries (split by ╔)
    entries = content.split("╔")
    if len(entries) <= last_n:
        return content
    
    return "╔" + "╔".join(entries[-last_n:])

def get_logs_by_date(date: str) -> str:
    """Get all logs for a specific date (YYYY-MM-DD format)."""
    if not LOG_FILE.exists():
        return "No activity logs found."
    
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    if not date in content:
        return f"No activity logs found for {date}."
    
    # Extract entries for the date
    entries = content.split("╔")
    matching = [e for e in entries if date in e]
    
    if not matching:
        return f"No activity logs found for {date}."
    
    return "╔" + "╔".join(matching)

def clear_logs():
    """Clear all logs."""
    if LOG_FILE.exists():
        LOG_FILE.unlink()

# Predefined activity constants
class Activities:
    # Teacher activities
    TEACHER_ADDED = "TEACHER_ADDED"
    TEACHER_REMOVED = "TEACHER_REMOVED"
    TEACHER_UPDATED = "TEACHER_UPDATED"
    
    # Class activities
    CLASS_ADDED = "CLASS_ADDED"
    CLASS_REMOVED = "CLASS_REMOVED"
    CLASS_UPDATED = "CLASS_UPDATED"
    
    # Timetable activities
    TIMETABLE_GENERATED = "TIMETABLE_GENERATED"
    TIMETABLE_CLEARED = "TIMETABLE_CLEARED"
    TIMETABLE_EXPORTED = "TIMETABLE_EXPORTED"
    
    # Configuration activities
    CONFIG_UPDATED = "CONFIG_UPDATED"
    DEMO_LOADED = "DEMO_LOADED"
    DATA_CLEARED = "DATA_CLEARED"
    
    # System
    APP_STARTED = "APP_STARTED"
    APP_ERROR = "APP_ERROR"
