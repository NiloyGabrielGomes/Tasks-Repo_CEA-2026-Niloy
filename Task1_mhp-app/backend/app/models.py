"""
Data models for the MHP application.
Core data structures using SQLModel.
"""

from datetime import datetime, date as dt_date
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field
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
    GLOBAL_WFH = "global_wfh"

class WorkLocationType(str, Enum):
    OFFICE = "Office"
    WFH = "WFH"

class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: UserRole = Field(default=UserRole.EMPLOYEE)
    team: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MealParticipation(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    meal_type: MealType
    date: dt_date = Field(index=True)
    is_participating: bool = Field(default=True)
    is_event_meal: bool = Field(default=False)
    updated_by: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    reason: Optional[str] = Field(default=None)

class WorkLocation(SQLModel, table=True):
    """Tracks where a user is working on a specific date."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    date: dt_date = Field(index=True)
    location: WorkLocationType = Field(default=WorkLocationType.OFFICE)
    updated_by: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SpecialDay(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    date: dt_date = Field(index=True, unique=True)
    day_type: str 
    note: Optional[str] = Field(default=None)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnnouncementStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"


class AnnouncementAudience(str, Enum):
    ALL = "all"
    TEAM_LEADS = "team_leads"


class Announcement(SQLModel, table=True):
    """An announcement that can be drafted, scheduled, or sent to employees."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str = Field(min_length=1, max_length=255)
    body: str
    audience: str = Field(default="all", max_length=100)
    status: AnnouncementStatus = Field(default=AnnouncementStatus.DRAFT, index=True)
    scheduled_at: Optional[datetime] = Field(default=None)
    published_at: Optional[datetime] = Field(default=None)
    created_by: str = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WFHPeriod(SQLModel, table=True):

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    employee_id: str = Field(foreign_key="user.id", index=True)
    start_date: dt_date = Field(index=True)
    end_date: dt_date = Field(index=True)
    reason: Optional[str] = Field(default=None, max_length=500)
    created_by: str = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScheduledMealPreference(SQLModel, table=True):

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    date: dt_date = Field(index=True)
    meal_type: MealType
    is_participating: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ===========================
# Models: Audit Logs, Event Meals, Policy Config
# ===========================

class EventMeal(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    date: dt_date = Field(index=True)
    meal_type: str = Field(max_length=50)  # e.g. "EventDinner"
    note: Optional[str] = Field(default=None, max_length=500)
    created_by: str = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLogEntry(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    actor_id: str = Field(foreign_key="user.id", index=True)
    target_user_id: Optional[str] = Field(default=None, foreign_key="user.id", index=True)
    action: str = Field(max_length=50, index=True)  # "create", "update", "delete"
    entity_type: str = Field(max_length=50, index=True)  # "meal_participation", "work_location", "policy", "event_meal"
    entity_id: Optional[str] = Field(default=None)
    field_changed: Optional[str] = Field(default=None, max_length=100)
    old_value: Optional[str] = Field(default=None)
    new_value: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)


class PolicyConfig(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    cutoff_time: str = Field(default="21:00", max_length=5)  # HH:MM format
    forward_planning_days: int = Field(default=7, ge=1)
    wfh_monthly_allowance: int = Field(default=5, ge=1)
    updated_by: Optional[str] = Field(default=None, foreign_key="user.id")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ===========================
# Constants
# ===========================

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

# Cutoff hour (24h format). Employees cannot change participation after this hour.
CUTOFF_HOUR = 21  # 9:00 PM

def create_default_participation(user_id: str, target_date: dt_date) -> list[MealParticipation]:
    return [
        MealParticipation(
            user_id=user_id,
            meal_type=meal_type,
            date=target_date,
            is_participating=(meal_type in DEFAULT_OPTED_IN_MEALS),
            updated_by=None,
            updated_at=datetime.utcnow()
        )
        for meal_type in MealType
    ]
