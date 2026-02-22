import json
import asyncio
import logging
from fastapi import APIRouter, Query, HTTPException, Request, status
from sse_starlette.sse import EventSourceResponse

from app.auth import get_user_from_token
from app.event_bus import (
    wait_for_change, get_last_change_timestamp, wait_for_announcement,
    register_headcount_client, unregister_headcount_client,
    register_announcement_client, unregister_announcement_client
)
from app.storage import get_all_participation, get_enabled_meals, get_all_users, get_work_locations_by_date

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stream", tags=["SSE"])


# ── Helpers ─────────────────────────────────────────────────────

def _build_headcount_payload(date_str: str | None = None) -> dict:
    from datetime import date as date_cls

    target_date = date_str or date_cls.today().isoformat()
    target_date_obj = date_cls.fromisoformat(target_date)
    participations = get_all_participation()
    users = get_all_users()
    config = get_enabled_meals()
    work_locations = get_work_locations_by_date(target_date_obj)

    user_map = {u.id: u for u in users}
    location_map = {wl.user_id: wl.location.value if hasattr(wl.location, 'value') else str(wl.location) for wl in work_locations}

    day_records = []
    for p in participations:
        p_date = p.date.isoformat() if hasattr(p.date, 'isoformat') else str(p.date)
        if p_date == target_date:
            day_records.append(p)

    # ── Totals by meal ──────────────────────────────────────────
    enabled_meal_names = [mt for mt, enabled in config.items() if enabled]
    meal_totals = {}
    for meal in enabled_meal_names:
        meal_totals[meal] = {
            "opted_in": 0,
            "opted_out": 0,
            "by_team": {},
            "by_location": {"Office": 0, "WFH": 0},
        }

    for record in day_records:
        user = user_map.get(record.user_id)
        team = user.team if user and user.team else "Unknown"
        location = location_map.get(record.user_id, "Office")
        meal_name = record.meal_type.value if hasattr(record.meal_type, 'value') else str(record.meal_type)

        if meal_name not in meal_totals:
            continue
        bucket = meal_totals[meal_name]

        if record.is_participating:
            bucket["opted_in"] += 1
            bucket["by_team"].setdefault(team, 0)
            bucket["by_team"][team] += 1
            if location in bucket["by_location"]:
                bucket["by_location"][location] += 1
            else:
                bucket["by_location"]["Office"] += 1
        else:
            bucket["opted_out"] += 1

    # ── Overall totals ──────────────────────────────────────────
    total_users = len(users)
    total_participating = len({
        r.user_id for r in day_records
        if r.is_participating
    })

    return {
        "date": target_date,
        "total_users": total_users,
        "total_participating": total_participating,
        "meals": meal_totals,
        "timestamp": get_last_change_timestamp(),
    }


# ── SSE Endpoint ────────────────────────────────────────────────

@router.get("/headcount")
async def headcount_stream(
    request: Request,
    token: str = Query(..., description="JWT token for authentication"),
    date: str | None = Query(None, description="Date in YYYY-MM-DD format (defaults to today)"),
):
    user = get_user_from_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    async def event_generator():
        """Yields SSE events until the client disconnects."""
        
        hc_event = register_headcount_client()
        ann_event = register_announcement_client()
        logger.info(f"SSE client connected, date={date}")

        try:
            payload = _build_headcount_payload(date)
            logger.info(f"SSE initial payload: participating={payload.get('total_participating')}, ts={payload.get('timestamp')}")
            yield {
                "event": "headcount",
                "data": json.dumps(payload),
            }

            while True:
                if await request.is_disconnected():
                    logger.info("SSE client disconnected")
                    break

                # Wait for whichever event fires first (headcount change OR announcement)
                headcount_task = asyncio.create_task(wait_for_change(hc_event, timeout=30.0))
                announcement_task = asyncio.create_task(wait_for_announcement(ann_event, timeout=30.0))

                done, pending = await asyncio.wait(
                    {headcount_task, announcement_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )

                headcount_changed = headcount_task in done and headcount_task.result() is True
                ann_data = announcement_task.result() if announcement_task in done else None

                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                if headcount_changed:
                    payload = _build_headcount_payload(date)
                    logger.info(f"SSE headcount update: participating={payload.get('total_participating')}, ts={payload.get('timestamp')}")
                    yield {
                        "event": "headcount",
                        "data": json.dumps(payload),
                    }

                if ann_data:
                    yield {
                        "event": "announcement",
                        "data": json.dumps(ann_data),
                    }

                if not headcount_changed and not ann_data:
                    yield {
                        "event": "heartbeat",
                        "data": "",
                    }
        except Exception as exc:
            logger.error(f"SSE generator error: {exc}", exc_info=True)
        finally:
            unregister_headcount_client(hc_event)
            unregister_announcement_client(ann_event)
            logger.info("SSE client unregistered")

    return EventSourceResponse(event_generator())