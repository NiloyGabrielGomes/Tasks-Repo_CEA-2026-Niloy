import logging
from datetime import date, datetime, timedelta, timezone

from src.config import settings

logger = logging.getLogger(__name__)

# Asia/Dhaka is UTC+6 (no DST)
DHAKA_UTC_OFFSET = timezone(timedelta(hours=6))


def get_dhaka_now() -> datetime:
    return datetime.now(DHAKA_UTC_OFFSET)


def get_dhaka_today() -> date:
    return get_dhaka_now().date()


_DEFAULT_CUTOFF_HOUR = 21
_DEFAULT_CUTOFF_MINUTE = 0


def _parse_cutoff_time(raw: str) -> tuple[int, int]:
    parts = raw.split(":")
    if len(parts) != 2:
        logger.warning(
            "Malformed CUTOFF_TIME '%s' (expected HH:MM). Falling back to %02d:%02d.",
            raw, _DEFAULT_CUTOFF_HOUR, _DEFAULT_CUTOFF_MINUTE,
        )
        return _DEFAULT_CUTOFF_HOUR, _DEFAULT_CUTOFF_MINUTE

    try:
        hour, minute = int(parts[0]), int(parts[1])
    except ValueError:
        logger.warning(
            "Non-numeric CUTOFF_TIME '%s'. Falling back to %02d:%02d.",
            raw, _DEFAULT_CUTOFF_HOUR, _DEFAULT_CUTOFF_MINUTE,
        )
        return _DEFAULT_CUTOFF_HOUR, _DEFAULT_CUTOFF_MINUTE

    if not (0 <= hour < 24 and 0 <= minute < 60):
        logger.warning(
            "CUTOFF_TIME '%s' out of range (hour 0-23, minute 0-59). "
            "Falling back to %02d:%02d.",
            raw, _DEFAULT_CUTOFF_HOUR, _DEFAULT_CUTOFF_MINUTE,
        )
        return _DEFAULT_CUTOFF_HOUR, _DEFAULT_CUTOFF_MINUTE

    return hour, minute


def get_cutoff_datetime(target_date: date) -> datetime:
    from src.services.policy_service import get_cutoff_time
    hour, minute = _parse_cutoff_time(get_cutoff_time())
    return datetime(
        target_date.year, target_date.month, target_date.day,
        hour, minute, 0,
        tzinfo=DHAKA_UTC_OFFSET,
    )


def is_past_cutoff(target_date: date) -> bool:
    now = get_dhaka_now()
    cutoff = get_cutoff_datetime(target_date)
    return now >= cutoff


def is_past_date(target_date: date) -> bool:
    return target_date < get_dhaka_today()


def is_within_forward_window(target_date: date) -> bool:
    today = get_dhaka_today()
    from src.services.policy_service import get_forward_planning_days
    max_date = today + timedelta(days=get_forward_planning_days())
    return target_date <= max_date

def validate_date_for_update(target_date: date) -> tuple[bool, str | None]:
    if is_past_date(target_date):
        return False, "Cannot update past dates. Please select today or a future date."

    if is_past_cutoff(target_date):
        return False, (
            f"Updates for {target_date.isoformat()} are closed. "
            f"The cutoff time is {get_cutoff_time()} (Asia/Dhaka)."
        )

    if not is_within_forward_window(target_date):
        return False, (
            f"Cannot update dates more than {get_forward_planning_days()} days ahead. "
            f"Maximum allowed date: {(get_dhaka_today() + timedelta(days=get_forward_planning_days())).isoformat()}."
        )

    return True, None


def parse_date_option(date_str: str | None) -> date:
    if not date_str:
        return get_dhaka_today() + timedelta(days=1)

    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid date format: '{date_str}'. Use YYYY-MM-DD.")


def format_date_display(d: date) -> str:
    return d.strftime("%A, %B %d, %Y")  # e.g. "Wednesday, March 04, 2026"
