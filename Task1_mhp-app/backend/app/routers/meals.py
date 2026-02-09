from fastapi import APIRouter, HTTPException, status, Query, Depends
from datetime import date, datetime
from pydantic import BaseModel
from typing import Dict, List
from app.models import User, MealType, MealParticipation, UserRole
from app import auth as auth_service
from app import storage

router = APIRouter()

# ===========================
# Response Models
# ===========================

class MealParticipationResponse(BaseModel):
    id: str
    user_id: str
    meal_type: str
    date: str
    is_participating: bool
    updated_by: str | None = None
    updated_at: str

class UserMealsResponse(BaseModel):
    date: str
    meals: List[MealParticipationResponse]

class HeadcountResponse(BaseModel):
    date: str
    headcount: Dict[str, int]

class UpdateParticipationRequest(BaseModel):
    is_participating: bool

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
    ]
    
    return UserMealsResponse(
        date=today.isoformat(),
        meals=meals
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
    ]
    
    return UserMealsResponse(
        date=target_date.isoformat(),
        meals=meals
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
    """
    # Check permissions
    if current_user.id != user_id and current_user.role not in [UserRole.TEAM_LEAD, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this user's meals"
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
    
    # Update participation
    updated = storage.update_participation(
        user_id=user_id,
        target_date=target_date,
        meal_type=meal_enum,
        is_participating=request.is_participating,
        updated_by=current_user.id
    )
    
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
# Get Headcount for Date
# ===========================

@router.get("/headcount/{target_date}", response_model=HeadcountResponse)
async def get_headcount(
    target_date: date,
    current_user: User = Depends(auth_service.require_team_lead)
):
    """
    Get headcount totals for each meal type on a specific date
    Team Leads and Admin only
    """
    headcount = storage.get_headcount_by_date(target_date)
    
    return HeadcountResponse(
        date=target_date.isoformat(),
        headcount=headcount
    )

# ===========================
# Get Today's Headcount
# ===========================

@router.get("/headcount/today", response_model=HeadcountResponse)
async def get_today_headcount(
    current_user: User = Depends(auth_service.require_team_lead)
):
    """
    Get headcount totals for each meal type for today
    Team Leads and Admin only
    """
    today = date.today()
    headcount = storage.get_headcount_by_date(today)
    
    return HeadcountResponse(
        date=today.isoformat(),
        headcount=headcount
    )
