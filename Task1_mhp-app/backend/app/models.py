"""
Data models for the MHP application.
Core data structures using Pydantic models.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
import uuid

class UserRole(str, Enum):
    EMPLOYEE = "employee"
    TEAM_LEAD = "team_lead"
    ADMIN = "admin"

class MealType(str, Enum):
    LUNCH = "lunch"
    SNACKS = "snacks"
    IFTAR = "iftar"
    EVENT_DINNER = "event_dinner"
    OPTIONAL_DINNER = "optional_dinner"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password_hash: str
    role: UserRole = UserRole.EMPLOYEE
    team: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123456",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "role": "employee",
                "team": "Midas",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z"
            }
        }



class MealParticipation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    meal_type: MealType
    date: date
    is_participating: bool = True
    updated_by: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "654321",
                "user_id": "123456",
                "meal_type": "lunch",
                "date": "2023-01-15",
                "is_participating": True,
                "updated_by": "team_lead_1",
                "updated_at": "2026-01-10T12:00:00Z"
            }
        }

# Meals that employees are opted-in for by default.
# Iftar is NOT a default meal — it requires admin configuration to enable.
DEFAULT_OPTED_IN_MEALS = {
    MealType.LUNCH,
    MealType.SNACKS,
    MealType.EVENT_DINNER,
    MealType.OPTIONAL_DINNER,
}

def create_default_participation(user_id: str, target_date: date) -> list[MealParticipation]:
    return [
        MealParticipation(
            user_id=user_id,
            meal_type=meal_type,
            date=target_date,
            is_participating=(meal_type in DEFAULT_OPTED_IN_MEALS),
            updated_by=None,
            updated_at=datetime.now()
        )
        for meal_type in MealType
    ]