from fastapi import APIRouter, HTTPException, Query, Depends, status
from datetime import date, datetime
from typing import Optional
from app.models import User, UserRole, SpecialDay, DayType, WorkLocationType, MealType
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

def _apply_global_wfh(target_date: date, admin_id: str) -> None:
 
    all_users = storage.get_all_users()
    active_users = [u for u in all_users if u.is_active]
    active_ids = [u.id for u in active_users]

    # 1. Set everyone to WFH
    for uid in active_ids:
        storage.set_work_location(
            user_id=uid,
            target_date=target_date,
            location=WorkLocationType.WFH,
            updated_by=admin_id,
        )

    # 2. Opt everyone out of every enabled meal
    enabled_meal_types = storage.get_enabled_meal_types() 
    opt_out_meals = {mt: False for mt in enabled_meal_types}

    if opt_out_meals and active_ids:
        storage.bulk_update_participation(
            user_ids=active_ids,
            target_date=target_date,
            meals=opt_out_meals,
            updated_by=admin_id,
            reason="Global Work From Home",
        )


def _revert_global_wfh(target_date: date, admin_id: str) -> None:
    """Undo Global WFH:
    1. Set everyone back to Office
    2. Default everyone to meals opted-OUT
    3. Re-apply any saved range preferences for users who had them
    """
    all_users = storage.get_all_users()
    active_users = [u for u in all_users if u.is_active]
    active_ids = [u.id for u in active_users]

    # 1. Set everyone back to Office
    for uid in active_ids:
        storage.set_work_location(
            user_id=uid,
            target_date=target_date,
            location=WorkLocationType.OFFICE,
            updated_by=admin_id,
        )

    # 2. Default everyone to meals opted-OUT
    enabled_meal_types = storage.get_enabled_meal_types()
    opt_out_meals = {mt: False for mt in enabled_meal_types}

    if opt_out_meals and active_ids:
        storage.bulk_update_participation(
            user_ids=active_ids,
            target_date=target_date,
            meals=opt_out_meals,
            updated_by=admin_id,
            reason="Global WFH ended – reverted to default",
        )

    # 3. Re-apply saved range preferences for users who had set them
    scheduled = storage.get_scheduled_meal_preferences_by_date(target_date)
    for uid, meals_dict in scheduled.items():
        if uid in active_ids:
            storage.bulk_update_participation(
                user_ids=[uid],
                target_date=target_date,
                meals=meals_dict,
                updated_by=uid,
                reason="Range preference restored after Global WFH",
            )

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
    # Ensure day_type is valid
    if isinstance(request.day_type, str):
        # Validate against Enum manually if passed as string due to schema relaxation
        try:
           pass 
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid day_type")

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

    day_type_val = request.day_type.value if hasattr(request.day_type, "value") else str(request.day_type)
    if day_type_val == "global_wfh":
        _apply_global_wfh(request.date, current_user.id)

    notify_headcount_change()

    return created


# ===========================
# Get Special Day by Date
# ===========================

@router.get("", response_model=Optional[SpecialDayResponse])
async def get_special_day(
    target_date: date = Query(..., alias="date", description="Date in YYYY-MM-DD"),
    current_user: User = Depends(auth_service.get_current_user),
):

    sd = storage.get_special_day_by_date(target_date)
    if sd is None:
        return None
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
    responses = [_to_response(sd) for sd in days]

    return SpecialDayListResponse(
        special_days=responses,
        total=len(responses),
    )


# ===========================
# Delete Special Day (Admin)
# ===========================

@router.delete("/{special_day_id}", status_code=status.HTTP_200_OK)
async def delete_special_day(
    special_day_id: str,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    # Look up the special day before deleting so we can check its type
    existing = storage.get_special_day_by_id(special_day_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Special day with id '{special_day_id}' not found",
        )

    was_global_wfh = False
    day_type_val = existing.day_type.value if hasattr(existing.day_type, "value") else str(existing.day_type)
    if day_type_val == "global_wfh":
        was_global_wfh = True
        target_date = existing.date

    deleted = storage.delete_special_day(special_day_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Special day with id '{special_day_id}' not found",
        )

    # Revert everyone to Office + re-opt into meals when Global WFH is turned off
    if was_global_wfh:
        _revert_global_wfh(target_date, current_user.id)

    notify_headcount_change()

    return {"message": "Special day deleted successfully", "id": special_day_id}
