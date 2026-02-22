import asyncio
from datetime import datetime, timezone

# ── Internal State ──────────────────────────────────────────────

_headcount_event: asyncio.Event | None = None
_last_change_timestamp: str | None = None


def _get_event() -> asyncio.Event:
    """
    Lazily initialise the asyncio.Event.
    Must be called inside a running event loop (i.e., during a request).
    """
    global _headcount_event
    if _headcount_event is None:
        _headcount_event = asyncio.Event()
    return _headcount_event


# ── Public API ──────────────────────────────────────────────────

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
    _get_event().set()


async def wait_for_change(timeout: float = 30.0) -> bool:

    event = _get_event()
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
    if _headcount_event is not None:
        _headcount_event.clear()
    _headcount_event = None
    _last_change_timestamp = None