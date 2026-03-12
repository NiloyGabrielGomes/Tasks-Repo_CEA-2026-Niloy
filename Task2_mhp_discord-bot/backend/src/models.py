from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid
# ── Enumerations ──────────────────────────────────────────────────────────────

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
class WorkLocationType(str, Enum):
    OFFICE = "office"
    WFH = "wfh"
class DayType(str, Enum):
    OFFICE_CLOSED = "office_closed"
    GOVERNMENT_HOLIDAY = "government_holiday"
    SPECIAL_EVENT = "special_event"
# ── User ──────────────────────────────────────────────────────────────────────

class User(BaseModel):
    discord_id: str
    name: str
    email: Optional[str] = None
    role: UserRole = UserRole.EMPLOYEE
    team: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
# ── Meal Participation ────────────────────────────────────────────────────────

class MealParticipation(BaseModel):
    user_id: str  # discord_id
    meal_type: MealType
    date: date
    is_participating: bool = True
    team: Optional[str] = None  # stamped from Discord role at write time
    updated_by: Optional[str] = None  # discord_id of actor
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    reason: Optional[str] = None
# ── Work Location ─────────────────────────────────────────────────────────────

class WorkLocation(BaseModel):
    user_id: str  # discord_id
    date: date
    location: WorkLocationType = WorkLocationType.OFFICE
    team: Optional[str] = None  # stamped from Discord role at write time
    updated_by: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
# ── Special Day ─────────────────────────────────────────────────────────────

class SpecialDay(BaseModel):
    date: date
    day_type: DayType
    note: Optional[str] = None
# ── Policy ─────────────────────────────────────────────────────────────────

class Policy(BaseModel):
    name: str
    value: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
