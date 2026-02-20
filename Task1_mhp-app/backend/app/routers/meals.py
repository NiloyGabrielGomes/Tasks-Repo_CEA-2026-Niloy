from fastapi import APIRouter, HTTPException, status, Query, Depends
from datetime import date, datetime
from app.models import User, MealType, MealParticipation, UserRole, CUTOFF_HOUR, ADMIN_CONTROLLED_MEALS
from app.auth import require_role
from app.schemas import (
    MealParticipationResponse,
    UserMealsResponse,
    HeadcountResponse,
    UpdateParticipationRequest,
    AdminParticipationOverrideRequest,
    MealConfigResponse,
    MealConfigUpdateRequest,
    BatchParticipationRequest,
    BatchParticipationResponse,
)
from app import auth as auth_service
from app import storage
from app.event_bus import notify_headcount_change

router = APIRouter()

# ===========================
# Helpers
# ===========================

def _is_cutoff_passed() -> bool:
    """Check if the current time is past the cutoff hour (9 PM)."""
    return datetime.now().hour >= CUTOFF_HOUR

# ===========================
# Meal Configuration (Admin only)
# ===========================

@router.get("/config", response_model=MealConfigResponse)
async def get_meal_config(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Get which meal types are currently enabled.
    All authenticated users can view this.
    """
    config = storage.get_enabled_meals()
    return MealConfigResponse(enabled_meals=config)

@router.put("/config", response_model=MealConfigResponse)
async def update_meal_config(
    request: MealConfigUpdateRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """
    Enable or disable a meal type. Admin only.
    Only admin-controlled meals (iftar, event_dinner) can be toggled.
    """
    # Validate meal type
    try:
        meal_enum = MealType(request.meal_type)
    except ValueError:
        valid_meals = ", ".join([m.value for m in MealType])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid meal type. Valid options: {valid_meals}"
        )
    
    if meal_enum not in ADMIN_CONTROLLED_MEALS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{request.meal_type} is always enabled and cannot be toggled"
        )
    
    config = storage.set_meal_enabled(request.meal_type, request.enabled)
    return MealConfigResponse(enabled_meals=config)

# ===========================
# Get User's Meal Participation for Today/Date
# ===========================

@router.get("/today", response_model=UserMealsResponse)
async def get_today_meals(current_user: User = Depends(auth_service.get_current_user)):
    """
    Get current user's meal participation for today
    """
    today = date.today()
    participation = storage.get_user_participation(current_user.id, today)
    enabled = storage.get_enabled_meal_types()
    
    meals = [
        MealParticipationResponse(
            id=record.id,
            user_id=record.user_id,
            meal_type=record.meal_type.value,
            date=record.date.isoformat(),
            is_participating=record.is_participating,
            updated_by=record.updated_by,
            updated_at=record.updated_at.isoformat()
        )
        for record in participation
        if record.meal_type.value in enabled
    ]
    
    return UserMealsResponse(
        date=today.isoformat(),
        meals=meals,
        cutoff_passed=_is_cutoff_passed()
    )

# ===========================
# Get User Meals for Specific Date
# ===========================

@router.get("/user/{user_id}", response_model=UserMealsResponse)
async def get_user_meals(
    user_id: str,
    target_date: date = Query(..., description="Target date in YYYY-MM-DD format"),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Get user's meal participation for a specific date
    User can view own meals, Team Leads/Admin can view any user
    """
    # Check permissions
    if current_user.id != user_id and current_user.role not in [UserRole.TEAM_LEAD, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this user's meals"
        )
    
    # Verify user exists
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    participation = storage.get_user_participation(user_id, target_date)
    
    # Filter to only enabled meals
    enabled_types = storage.get_enabled_meal_types()
    
    meals = [
        MealParticipationResponse(
            id=record.id,
            user_id=record.user_id,
            meal_type=record.meal_type.value,
            date=record.date.isoformat(),
            is_participating=record.is_participating,
            updated_by=record.updated_by,
            updated_at=record.updated_at.isoformat()
        )
        for record in participation
        if record.meal_type in enabled_types
    ]
    
    return UserMealsResponse(
        date=target_date.isoformat(),
        meals=meals,
        cutoff_passed=_is_cutoff_passed()
    )

# ===========================
# Update Meal Participation
# ===========================

@router.put("/{user_id}/{target_date}/{meal_type}", response_model=MealParticipationResponse)
async def update_meal_participation(
    user_id: str,
    target_date: date,
    meal_type: str,
    request: UpdateParticipationRequest,
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Update meal participation for a user
    User can update own meals, Team Leads/Admin can update for others
    Employees are blocked after 9 PM cutoff; Admin/TL are exempt.
    """
    # Check permissions
    if current_user.id != user_id and current_user.role not in [UserRole.TEAM_LEAD, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this user's meals"
        )
    
    blocked, reason = storage.is_participation_blocked(target_date)
    if blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=reason,
        )

    if current_user.role == UserRole.EMPLOYEE and target_date == date.today() and _is_cutoff_passed():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Meal participation changes are locked after 9:00 PM. You can update again tomorrow morning."
        )
    
    # Verify user exists
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate meal type
    try:
        meal_enum = MealType(meal_type)
    except ValueError:
        valid_meals = ", ".join([m.value for m in MealType])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid meal type. Valid options: {valid_meals}"
        )
    
    # Verify the meal type is currently enabled
    enabled_types = storage.get_enabled_meal_types()
    if meal_enum not in enabled_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The meal type '{meal_type}' is not currently enabled"
        )
    
    # Update participation
    updated = storage.update_participation(
        user_id=user_id,
        target_date=target_date,
        meal_type=meal_enum,
        is_participating=request.is_participating,
        updated_by=current_user.id
    )

    # Notify SSE clients of headcount change
    notify_headcount_change()
    
    return MealParticipationResponse(
        id=updated.id,
        user_id=updated.user_id,
        meal_type=updated.meal_type.value,
        date=updated.date.isoformat(),
        is_participating=updated.is_participating,
        updated_by=updated.updated_by,
        updated_at=updated.updated_at.isoformat()
    )

# ===========================
# Admin/Team Lead Override Participation
# ===========================

@router.post("/participation/admin", response_model=MealParticipationResponse)
async def admin_update_participation(
    request: AdminParticipationOverrideRequest,
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN]))
):
    """
    Team Lead or Admin updates participation on behalf of an employee.
    Team Leads can only update users in their team.
    Records who made the update for audit trail.
    """
    # Get target user
    target_user = storage.get_user_by_id(request.user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Team leads can only update their own team
    if current_user.role == UserRole.TEAM_LEAD and current_user.team != target_user.team:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update users in your team"
        )

    blocked, reason = storage.is_participation_blocked(date.today())
    if blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=reason,
        )
    
    # Validate meal type
    try:
        meal_enum = MealType(request.meal_type)
    except ValueError:
        valid_meals = ", ".join([m.value for m in MealType])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid meal type. Valid options: {valid_meals}"
        )
    
    # Verify the meal type is currently enabled
    enabled_types = storage.get_enabled_meal_types()
    if meal_enum not in enabled_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The meal type '{request.meal_type}' is not currently enabled"
        )
    
    today = date.today()
    
    # Update participation with audit trail (updated_by = admin/TL id)
    updated = storage.update_participation(
        user_id=request.user_id,
        target_date=today,
        meal_type=meal_enum,
        is_participating=request.is_participating,
        updated_by=current_user.id
    )

    # Notify SSE clients of headcount change
    notify_headcount_change()
    
    return MealParticipationResponse(
        id=updated.id,
        user_id=updated.user_id,
        meal_type=updated.meal_type.value,
        date=updated.date.isoformat(),
        is_participating=updated.is_participating,
        updated_by=updated.updated_by,
        updated_at=updated.updated_at.isoformat()
    )

# ===========================
# Batch Admin/Team Lead Override Participation
# ===========================

@router.post("/participation/admin/batch", response_model=BatchParticipationResponse)
async def batch_admin_update_participation(
    payload: BatchParticipationRequest,
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN])),
):
    """
    Accept multiple participation updates in a single request.
    Replaces the pattern of calling POST /participation/admin once per meal type.
    Team Leads can only update users in their own team.
    """
    results = []
    succeeded = 0
    failed = 0
    today = date.today()

    blocked, reason = storage.is_participation_blocked(today)
    if blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=reason,
        )

    enabled_types = storage.get_enabled_meal_types()

    for item in payload.updates:
        try:
            target_user = storage.get_user_by_id(item.user_id)
            if not target_user:
                raise ValueError("User not found")

            if current_user.role == UserRole.TEAM_LEAD and current_user.team != target_user.team:
                raise ValueError("Can only update users in your team")

            try:
                meal_enum = MealType(item.meal_type)
            except ValueError:
                valid_meals = ", ".join([m.value for m in MealType])
                raise ValueError(f"Invalid meal type. Valid options: {valid_meals}")

            if meal_enum not in enabled_types:
                raise ValueError(f"The meal type '{item.meal_type}' is not currently enabled")

            storage.update_participation(
                user_id=item.user_id,
                target_date=today,
                meal_type=meal_enum,
                is_participating=item.is_participating,
                updated_by=current_user.id,
            )

            results.append({
                "user_id": item.user_id,
                "meal_type": item.meal_type,
                "success": True,
                "message": "Updated",
            })
            succeeded += 1

        except Exception as exc:
            results.append({
                "user_id": item.user_id,
                "meal_type": item.meal_type,
                "success": False,
                "message": str(exc),
            })
            failed += 1

    # Notify SSE clients of headcount change (if any succeeded)
    if succeeded > 0:
        notify_headcount_change()

    return BatchParticipationResponse(
        total=len(payload.updates),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )

# ===========================
# Get Team Headcount for Today
# ===========================

@router.get("/headcount/team/today", response_model=HeadcountResponse)
async def get_team_headcount_today(
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN]))
):
    """
    Get headcount for the team lead's team for today
    """
    today = date.today()
    headcount = storage.get_headcount_by_date_and_team(today, current_user.team)
    enabled_types = storage.get_enabled_meal_types()
    headcount = {k: v for k, v in headcount.items() if MealType(k) in enabled_types}
    team_users = storage.get_users_by_team(current_user.team)
    total_active = len([u for u in team_users if u.is_active])
    
    return HeadcountResponse(
        date=today.isoformat(),
        headcount=headcount,
        total_employees=total_active
    )

# ===========================
# Get Team Headcount for Specific Date
# ===========================

@router.get("/headcount/team/{target_date}", response_model=HeadcountResponse)
async def get_team_headcount(
    target_date: date,
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN]))
):
    """
    Get headcount for the team lead's team for a specific date
    """
    headcount = storage.get_headcount_by_date_and_team(target_date, current_user.team)
    enabled_types = storage.get_enabled_meal_types()
    headcount = {k: v for k, v in headcount.items() if MealType(k) in enabled_types}
    team_users = storage.get_users_by_team(current_user.team)
    total_active = len([u for u in team_users if u.is_active])
    
    return HeadcountResponse(
        date=target_date.isoformat(),
        headcount=headcount,
        total_employees=total_active
    )

# ===========================
# Get Today's Headcount
# ===========================

@router.get("/headcount/today", response_model=HeadcountResponse)
async def get_today_headcount(
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN]))
):
    """
    Get headcount totals for each meal type for today
    Team Leads and Admin only
    """
    today = date.today()
    headcount = storage.get_headcount_by_date(today)
    enabled_types = storage.get_enabled_meal_types()
    headcount = {k: v for k, v in headcount.items() if MealType(k) in enabled_types}
    all_users = storage.get_all_users()
    total_active = len([u for u in all_users if u.is_active])
    
    return HeadcountResponse(
        date=today.isoformat(),
        headcount=headcount,
        total_employees=total_active
    )

# ===========================
# Get Headcount for Date
# ===========================

@router.get("/headcount/{target_date}", response_model=HeadcountResponse)
async def get_headcount(
    target_date: date,
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN]))
):
    """
    Get headcount totals for each meal type on a specific date
    Team Leads and Admin only
    """
    headcount = storage.get_headcount_by_date(target_date)
    enabled_types = storage.get_enabled_meal_types()
    headcount = {k: v for k, v in headcount.items() if MealType(k) in enabled_types}
    all_users = storage.get_all_users()
    total_active = len([u for u in all_users if u.is_active])
    
    return HeadcountResponse(
        date=target_date.isoformat(),
        headcount=headcount,
        total_employees=total_active
    )
