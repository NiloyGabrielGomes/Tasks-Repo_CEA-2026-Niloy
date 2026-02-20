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

class DayType(str, Enum):
    OFFICE_CLOSED = "officeclosed"
    GOVERNMENT_HOLIDAY = "governmentholiday"
    SPECIAL_EVENT = "specialevent"


class WorkLocationType(str, Enum):
    OFFICE = "Office"
    WFH = "WFH"

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
    reason: Optional[str] = None

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

DEFAULT_OPTED_IN_MEALS = {
    MealType.LUNCH,
    MealType.SNACKS,
    MealType.OPTIONAL_DINNER,
}

# Meals that require admin to enable before they appear to employees.
ADMIN_CONTROLLED_MEALS = {
    MealType.IFTAR,
    MealType.EVENT_DINNER,
}


class WorkLocation(BaseModel):
    """Tracks where a user is working on a specific date."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: date
    location: WorkLocationType = WorkLocationType.OFFICE
    updated_by: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "wl-001",
                "user_id": "user-1",
                "date": "2026-02-19",
                "location": "Office",
                "updated_by": "user-1",
                "updated_at": "2026-02-19T08:00:00"
            }
        }

# Cutoff hour (24h format). Employees cannot change participation after this hour.
CUTOFF_HOUR = 21  # 9:00 PM

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

class SpecialDay(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: date
    day_type: DayType
    note: str | None = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "sd-001",
                "date": "2026-03-26",
                "day_type": "governmentholiday",
                "note": "Independence Day",
                "created_by": "admin-user-id",
                "created_at": "2026-02-19T10:30:00"
            }
        }