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



