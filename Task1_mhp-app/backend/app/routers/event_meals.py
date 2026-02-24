from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import date
from app.models import User, UserRole, EventMeal
from app.auth import get_current_user, require_role
from app.schemas import EventMealCreate, EventMealResponse, EventMealListResponse, MessageResponse
from app import storage
from app import utils

router = APIRouter()

@router.post("/", response_model=EventMealResponse, status_code=status.HTTP_201_CREATED)
async def create_event_meal(
    request: EventMealCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):

    event_meal = EventMeal(
        date=request.date,
        meal_type=request.meal_type,
        note=request.note,
        created_by=current_user.id
    )
    return storage.create_event_meal(event_meal)

@router.get("/", response_model=EventMealListResponse)
async def list_event_meals(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):

    events = storage.get_all_event_meals(start_date=start_date, end_date=end_date)
    return EventMealListResponse(event_meals=events, total=len(events))

@router.get("/today", response_model=EventMealListResponse)
async def get_today_event_meals(
    current_user: User = Depends(get_current_user)
):

    today = utils.get_today()
    events = storage.get_event_meals_by_date(today)
    return EventMealListResponse(event_meals=events, total=len(events))

@router.get("/{event_meal_id}", response_model=EventMealResponse)
async def get_event_meal(
    event_meal_id: str,
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):

    event = storage.get_event_meal_by_id(event_meal_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event meal not found")
    return event

@router.delete("/{event_meal_id}", response_model=MessageResponse)
async def delete_event_meal(
    event_meal_id: str,
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):

    if not storage.delete_event_meal(event_meal_id):
        raise HTTPException(status_code=404, detail="Event meal not found")
    return MessageResponse(message="Event meal deleted successfully")
