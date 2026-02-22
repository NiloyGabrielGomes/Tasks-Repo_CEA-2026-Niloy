import asyncio
from datetime import datetime, timezone
from typing import Optional

# ── Internal State ──────────────────────────────────────────────

_headcount_event: asyncio.Event = asyncio.Event()
_last_change_timestamp: str | None = None

_announcement_event: asyncio.Event = asyncio.Event()
_latest_announcement: Optional[dict] = None


# ── Headcount Public API ────────────────────────────────────────

def notify_headcount_change() -> None:
    """
    Signal all waiting SSE consumers that headcount data has changed.

    Call this after any operation that affects meal participation:
      - PUT  /api/meals/participation
      - POST /api/meals/participation/admin
      - POST /api/meals/participation/bulk
      - POST /api/special-days
      - DELETE /api/special-days/{id}
      - PUT  /api/work-locations
      - PUT  /api/work-locations/admin
    """
    global _last_change_timestamp
    _last_change_timestamp = datetime.now(timezone.utc).isoformat()
    _headcount_event.set()


async def wait_for_change(timeout: float = 30.0) -> bool:

    event = _headcount_event
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)

        event.clear()
        return True
    except asyncio.TimeoutError:
        return False


def get_last_change_timestamp() -> str | None:

    return _last_change_timestamp


def reset() -> None:
    #Reset the event bus state.  Intended for testing only.

    global _headcount_event, _last_change_timestamp
    global _announcement_event, _latest_announcement
    if _headcount_event is not None:
        _headcount_event.clear()
    _headcount_event = None
    _last_change_timestamp = None
    if _announcement_event is not None:
        _announcement_event.clear()
    _announcement_event = None
    _latest_announcement = None


# ── Announcement Public API ─────────────────────────────────────

def notify_announcement(data: dict) -> None:

    global _latest_announcement
    _latest_announcement = data
    _announcement_event.set()


async def wait_for_announcement(timeout: float = 30.0) -> Optional[dict]:
    global _latest_announcement
    try:
        await asyncio.wait_for(_announcement_event.wait(), timeout=timeout)
        _announcement_event.clear()
        return _latest_announcement
    except asyncio.TimeoutError:
        return None


def get_latest_announcement() -> Optional[dict]:
    return _latest_announcement