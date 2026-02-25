from fastapi import APIRouter, HTTPException, Query, Depends, status
from datetime import date
from app.models import User, UserRole, WorkLocationType
from app.auth import require_role
from app import auth as auth_service
from app import storage
from app.event_bus import notify_headcount_change
from app.schemas import (
    WorkLocationUpdate,
    AdminWorkLocationUpdate,
    WorkLocationResponse,
    WorkLocationListResponse,
)

router = APIRouter(prefix="/api/work-locations", tags=["Work Locations"])


# ── Helpers ─────────────────────────────────────────────────────

def _to_response(wl) -> WorkLocationResponse:
    return WorkLocationResponse(
        id=wl.id,
        user_id=wl.user_id,
        date=wl.date.isoformat() if hasattr(wl.date, "isoformat") else str(wl.date),
        location=wl.location.value if hasattr(wl.location, "value") else str(wl.location),
        updated_by=wl.updated_by,
        updated_at=wl.updated_at.isoformat() if hasattr(wl.updated_at, "isoformat") else str(wl.updated_at),
    )


# ===========================
# Set Own Work Location
# ===========================

@router.put("", response_model=WorkLocationResponse)
async def set_my_work_location(
    request: WorkLocationUpdate,
    current_user: User = Depends(auth_service.get_current_user),
):
    wl = storage.set_work_location(
        user_id=current_user.id,
        target_date=request.date,
        location=request.location,
        updated_by=current_user.id,
    )
    notify_headcount_change()
    return wl


# ===========================
# Get Own Work Location
# ===========================

@router.get("/me", response_model=WorkLocationResponse)
async def get_my_work_location(
    target_date: date = Query(None, description="Date in YYYY-MM-DD (defaults to today)"),
    current_user: User = Depends(auth_service.get_current_user),
):
    """Get the current user's work location for a date."""
    day = target_date or date.today()
    wl = storage.get_work_location(current_user.id, day)
    if not wl:
        # Return default (Office)
        return WorkLocationResponse(
            id="",
            user_id=current_user.id,
            date=day.isoformat(),
            location=WorkLocationType.OFFICE.value,
            updated_by=None,
            updated_at="",
        )
    return _to_response(wl)


# ===========================
# Get All Locations for a Date (TL/Admin)
# ===========================

@router.get("/date", response_model=WorkLocationListResponse)
async def get_locations_by_date(
    target_date: date = Query(None, description="Date in YYYY-MM-DD (defaults to today)"),
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN])),
):
    """Get all users' work locations for a date. Team Leads see own team only."""
    day = target_date or date.today()
    all_locations = storage.get_work_locations_by_date(day)

    if current_user.role == UserRole.TEAM_LEAD:
        team_users = storage.get_users_by_team(current_user.team)
        team_ids = {u.id for u in team_users}
        all_locations = [wl for wl in all_locations if wl.user_id in team_ids]

    responses = [_to_response(wl) for wl in all_locations]
    return WorkLocationListResponse(
        date=day.isoformat(),
        locations=responses,
        total=len(responses),
    )


# ===========================
# Admin Set Any User's Work Location
# ===========================

@router.put("/admin", response_model=WorkLocationResponse)
async def admin_set_work_location(
    request: AdminWorkLocationUpdate,
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN])),
):
    """
    Admin/Team Lead sets a user's work location.
    Team Leads can only update their own team members.
    """
    target_user = storage.get_user_by_id(request.user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if current_user.role == UserRole.TEAM_LEAD and current_user.team != target_user.team:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update work locations for your own team members",
        )

    wl = storage.set_work_location(
        user_id=request.user_id,
        target_date=request.date,
        location=request.location,
        updated_by=current_user.id,
    )
    notify_headcount_change()
    return _to_response(wl)
