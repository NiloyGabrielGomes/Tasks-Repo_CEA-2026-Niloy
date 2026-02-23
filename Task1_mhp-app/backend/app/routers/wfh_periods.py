from datetime import date as dt_date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends, status

from app.models import User, UserRole, WFHPeriod, WorkLocationType
from app.auth import require_role
from app import auth as auth_service
from app import storage
from app.event_bus import notify_headcount_change
from app.schemas import (
    WFHPeriodCreate,
    WFHPeriodUpdate,
    WFHPeriodResponse,
    WFHPeriodListResponse,
)

router = APIRouter(prefix="/api/wfh-periods", tags=["WFH Periods"])


# ── Helpers ──────────────────────────────────────────────────────────────────

def _to_response(period: WFHPeriod, user: Optional[User] = None) -> WFHPeriodResponse:
    return WFHPeriodResponse(
        id=period.id,
        employee_id=period.employee_id,
        employee_name=user.name if user else None,
        employee_team=user.team if user else None,
        start_date=period.start_date,
        end_date=period.end_date,
        reason=period.reason,
        created_by=period.created_by,
        created_at=period.created_at,
        updated_at=period.updated_at,
    )


def _build_response_with_user_lookup(period: WFHPeriod) -> WFHPeriodResponse:
    employee = storage.get_user_by_id(period.employee_id)
    return _to_response(period, employee)


def _validate_dates(start_date: dt_date, end_date: dt_date) -> None:
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be on or after start_date.",
        )


def _check_permission_for_employee(
    current_user: User,
    employee_id: str,
) -> User:
    target = storage.get_user_by_id(employee_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")

    if current_user.role == UserRole.ADMIN:
        return target

    if current_user.role == UserRole.TEAM_LEAD:
        if current_user.team and target.team == current_user.team:
            return target
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team leads can only manage WFH periods for members of their own team.",
        )

    # Employee — can only manage their own periods
    if current_user.id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employees can only manage their own WFH periods.",
        )
    return target


def _check_overlap(
    employee_id: str,
    start_date: dt_date,
    end_date: dt_date,
    exclude_id: Optional[str] = None,
) -> None:
    overlaps = storage.get_overlapping_wfh_periods(employee_id, start_date, end_date, exclude_id)
    if overlaps:
        clash = overlaps[0]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Overlaps with existing WFH period "
                f"{clash.start_date.isoformat()} – {clash.end_date.isoformat()} "
                f"(id: {clash.id})."
            ),
        )


# ── POST /api/wfh-periods ─────────────────────────────────────────────────────

@router.post("", response_model=WFHPeriodResponse, status_code=status.HTTP_201_CREATED)
async def create_wfh_period(
    body: WFHPeriodCreate,
    current_user: User = Depends(auth_service.get_current_user),
):
    employee = _check_permission_for_employee(current_user, body.employee_id)
    _validate_dates(body.start_date, body.end_date)
    _check_overlap(body.employee_id, body.start_date, body.end_date)

    period = WFHPeriod(
        employee_id=body.employee_id,
        start_date=body.start_date,
        end_date=body.end_date,
        reason=body.reason,
        created_by=current_user.id,
    )
    saved = storage.create_wfh_period(period)
    
    # Automatically set WorkLocation to WFH for each day in the period (Soft Opt Out)
    curr_date = body.start_date
    while curr_date <= body.end_date:
        # Check if Global WFH is active? No, we proceed with setting WFH.
        storage.set_work_location(
            user_id=body.employee_id,
            target_date=curr_date,
            location=WorkLocationType.WFH,
            updated_by=current_user.id
        )
        curr_date += timedelta(days=1)
        
    notify_headcount_change()

    return _to_response(saved, employee)


# ── GET /api/wfh-periods ─────────────────────────────────────────────────────

@router.get("", response_model=WFHPeriodListResponse)
async def list_wfh_periods(
    employee_id: Optional[str] = Query(None, description="Filter by specific employee"),
    team: Optional[str] = Query(None, description="Filter by team name (TL/Admin only)"),
    start_date: Optional[dt_date] = Query(None, description="Only periods that end on/after this date"),
    end_date: Optional[dt_date] = Query(None, description="Only periods that start on/before this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Results per page"),
    current_user: User = Depends(auth_service.get_current_user),
):

    # Scope based on role
    if current_user.role == UserRole.EMPLOYEE:
        employee_id = current_user.id
        team = None
    elif current_user.role == UserRole.TEAM_LEAD:
        if employee_id:
            _check_permission_for_employee(current_user, employee_id)
        else:
            # Default to the TL's own team
            team = team or current_user.team

    periods, total = storage.get_wfh_periods(
        employee_id=employee_id,
        team=team,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )

    # Bulk-fetch employee info for display
    user_cache: dict[str, User] = {}
    for p in periods:
        if p.employee_id not in user_cache:
            u = storage.get_user_by_id(p.employee_id)
            if u:
                user_cache[p.employee_id] = u

    return WFHPeriodListResponse(
        periods=[_to_response(p, user_cache.get(p.employee_id)) for p in periods],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── PATCH /api/wfh-periods/:id ────────────────────────────────────────────────

@router.patch("/{period_id}", response_model=WFHPeriodResponse)
async def update_wfh_period(
    period_id: str,
    body: WFHPeriodUpdate,
    current_user: User = Depends(auth_service.get_current_user),
):
    period = storage.get_wfh_period_by_id(period_id)
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WFH period not found.")

    # Permission: creator or admin
    if current_user.role != UserRole.ADMIN and period.created_by != current_user.id:
        if period.employee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update WFH periods you created.",
            )

    # Merge with existing values
    new_start = body.start_date if body.start_date is not None else period.start_date
    new_end = body.end_date if body.end_date is not None else period.end_date
    new_reason = body.reason if body.reason is not None else period.reason

    _validate_dates(new_start, new_end)
    _check_overlap(period.employee_id, new_start, new_end, exclude_id=period_id)

    updated = storage.update_wfh_period(
        period_id=period_id,
        start_date=new_start,
        end_date=new_end,
        reason=new_reason,
    )
    return _build_response_with_user_lookup(updated)


# ── DELETE /api/wfh-periods/:id ───────────────────────────────────────────────

@router.delete("/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wfh_period(
    period_id: str,
    current_user: User = Depends(auth_service.get_current_user),
):
    period = storage.get_wfh_period_by_id(period_id)
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WFH period not found.")

    # Permission: creator, the employee themselves, or admin
    is_admin = current_user.role == UserRole.ADMIN
    is_creator = period.created_by == current_user.id
    is_own = period.employee_id == current_user.id

    if not (is_admin or is_creator or is_own):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete WFH periods you created or that belong to you.",
        )

    storage.delete_wfh_period(period_id)
