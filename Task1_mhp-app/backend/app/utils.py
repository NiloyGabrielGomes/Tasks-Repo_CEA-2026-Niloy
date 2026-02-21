from datetime import datetime, date, time, timezone
import os

from zoneinfo import ZoneInfo


# Default to Asia/Dhaka or UTC based on preference, but configurable via env
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Dhaka")

def get_timezone():
    if APP_TIMEZONE == "UTC":
        return timezone.utc
    try:
        return ZoneInfo(APP_TIMEZONE)
    except Exception:
        return timezone.utc

def get_current_time() -> datetime:
    """Returns the current time in the application's configured timezone."""
    return datetime.now(get_timezone())

def get_today() -> date:
    """Returns the current date in the application's configured timezone."""
    return get_current_time().date()

def is_cutoff_passed(cutoff_hour: int) -> bool:
    """Checks if the current time is past the cutoff hour in the app's timezone."""
    return get_current_time().hour >= cutoff_hour
