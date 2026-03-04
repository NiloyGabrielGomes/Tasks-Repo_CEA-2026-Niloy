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


def get_cutoff_datetime(target_date: date) -> datetime:
    hour, minute = map(int, settings.CUTOFF_TIME.split(":"))
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
    max_date = today + timedelta(days=settings.FORWARD_PLANNING_DAYS)
    return target_date <= max_date

def validate_date_for_update(target_date: date) -> tuple[bool, str | None]:
    if is_past_date(target_date):
        return False, "Cannot update past dates. Please select today or a future date."

    if is_past_cutoff(target_date):
        return False, (
            f"Updates for {target_date.isoformat()} are closed. "
            f"The cutoff time is {settings.CUTOFF_TIME} (Asia/Dhaka)."
        )

    if not is_within_forward_window(target_date):
        return False, (
            f"Cannot update dates more than {settings.FORWARD_PLANNING_DAYS} days ahead. "
            f"Maximum allowed date: {(get_dhaka_today() + timedelta(days=settings.FORWARD_PLANNING_DAYS)).isoformat()}."
        )

    return True, None


def parse_date_option(date_str: str | None) -> date:
    if not date_str:
        return get_dhaka_today()

    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid date format: '{date_str}'. Use YYYY-MM-DD.")


def format_date_display(d: date) -> str:
    return d.strftime("%A, %B %d, %Y")  # e.g. "Wednesday, March 04, 2026"
