import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Set

logger = logging.getLogger(__name__)

# ── Internal State ──────────────────────────────────────────────

_headcount_events: Set[asyncio.Event] = set()
_last_change_timestamp: str | None = None

_announcement_events: Set[asyncio.Event] = set()
_latest_announcement: Optional[dict] = None


# ── Headcount Public API ────────────────────────────────────────

def notify_headcount_change() -> None:
    """
    Signal all waiting SSE consumers that headcount data has changed.
    """
    global _last_change_timestamp
    _last_change_timestamp = datetime.now(timezone.utc).isoformat()
    num_clients = len(_headcount_events)
    logger.info(f"notify_headcount_change: ts={_last_change_timestamp}, clients={num_clients}")
    for event in list(_headcount_events):
        event.set()


async def wait_for_change(client_event: asyncio.Event, timeout: float = 30.0) -> bool:
    try:
        await asyncio.wait_for(client_event.wait(), timeout=timeout)
        client_event.clear()
        return True
    except asyncio.TimeoutError:
        return False


def get_last_change_timestamp() -> str | None:
    return _last_change_timestamp


def register_headcount_client() -> asyncio.Event:
    event = asyncio.Event()
    _headcount_events.add(event)
    return event

def unregister_headcount_client(event: asyncio.Event) -> None:
    _headcount_events.discard(event)


def reset() -> None:
    #Reset the event bus state.  Intended for testing only.
    global _last_change_timestamp, _latest_announcement
    _headcount_events.clear()
    _last_change_timestamp = None
    _announcement_events.clear()
    _latest_announcement = None


# ── Announcement Public API ─────────────────────────────────────

def notify_announcement(data: dict) -> None:
    global _latest_announcement
    _latest_announcement = data
    for event in list(_announcement_events):
        event.set()


async def wait_for_announcement(client_event: asyncio.Event, timeout: float = 30.0) -> Optional[dict]:
    global _latest_announcement
    try:
        await asyncio.wait_for(client_event.wait(), timeout=timeout)
        client_event.clear()
        return _latest_announcement
    except asyncio.TimeoutError:
        return None

def register_announcement_client() -> asyncio.Event:
    event = asyncio.Event()
    _announcement_events.add(event)
    return event

def unregister_announcement_client(event: asyncio.Event) -> None:
    _announcement_events.discard(event)

def get_latest_announcement() -> Optional[dict]:
    return _latest_announcement