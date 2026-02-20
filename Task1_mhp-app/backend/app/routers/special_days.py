from fastapi import APIRouter, HTTPException, Query, Depends, status
from datetime import date, datetime
from app.models import User, UserRole, SpecialDay, DayType
from app.auth import require_role
from app import auth as auth_service
from app import storage
from app.event_bus import notify_headcount_change
from app.schemas import (
    SpecialDayCreate,
    SpecialDayResponse,
    SpecialDayListResponse,
)

router = APIRouter(prefix="/api/special-days", tags=["Special Days"])


# ── Helpers ─────────────────────────────────────────────────────

def _to_response(sd: SpecialDay) -> SpecialDayResponse:
    return SpecialDayResponse(
        id=sd.id,
        date=sd.date.isoformat() if hasattr(sd.date, "isoformat") else str(sd.date),
        day_type=sd.day_type.value if hasattr(sd.day_type, "value") else str(sd.day_type),
        note=sd.note,
        created_by=sd.created_by,
        created_at=sd.created_at.isoformat() if hasattr(sd.created_at, "isoformat") else str(sd.created_at),
    )


# ===========================
# Create Special Day (Admin)
# ===========================

@router.post("", response_model=SpecialDayResponse, status_code=status.HTTP_201_CREATED)
async def create_special_day(
    request: SpecialDayCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):

    sd = SpecialDay(
        date=request.date,
        day_type=request.day_type,
        note=request.note,
        created_by=current_user.id,
        created_at=datetime.now(),
    )

    try:
        created = storage.create_special_day(sd)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    notify_headcount_change()

    return created


# ===========================
# Get Special Day by Date
# ===========================

@router.get("", response_model=SpecialDayResponse)
async def get_special_day(
    target_date: date = Query(..., alias="date", description="Date in YYYY-MM-DD"),
    current_user: User = Depends(auth_service.get_current_user),
):

    sd = storage.get_special_day_by_date(target_date)
    if sd is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No special day found for {target_date.isoformat()}",
        )
    return sd


# ===========================
# Get Special Days in Range
# ===========================

@router.get("/range", response_model=SpecialDayListResponse)
async def get_special_days_range(
    start: date = Query(..., description="Start date (inclusive) YYYY-MM-DD"),
    end: date = Query(..., description="End date (inclusive) YYYY-MM-DD"),
    current_user: User = Depends(auth_service.get_current_user),
):

    if end < start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be on or after start date",
        )

    days = storage.get_special_days_range(start, end)

    return SpecialDayListResponse(
        special_days=days,
        total=len(days),
    )


# ===========================
# Delete Special Day (Admin)
# ===========================

@router.delete("/{special_day_id}", status_code=status.HTTP_200_OK)
async def delete_special_day(
    special_day_id: str,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):

    deleted = storage.delete_special_day(special_day_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Special day with id '{special_day_id}' not found",
        )

    notify_headcount_change()

    return {"message": "Special day deleted successfully", "id": special_day_id}
