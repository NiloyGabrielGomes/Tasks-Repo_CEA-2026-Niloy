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



