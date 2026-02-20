from datetime import datetime, date
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, EmailStr
from app.models import UserRole, MealType, WorkLocationType, DayType

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "password": "secure_password"
            }
        }

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: 'UserResponse'

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "123456",
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "role": "employee",
                    "team": "Midas"
                }
            }
        }


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole
    team: Optional[str] = None
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123456",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "role": "employee",
                "team": "Midas",
                "is_active": True
            }
        }

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.EMPLOYEE
    team: Optional[str] = Field(None, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "password": "secure_password",
                "role": "employee",
                "team": "Midas"
            }
        }


class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6)
    team: Optional[str] = Field(None, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@company.com",
                "password": "securepassword123",
                "team": "Engineering"
            }
        }


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    team: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Updated Doe",
                "role": "TeamLead",
                "team": "Engineering",
                "is_active": True
            }
        }


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "id": "user-1",
                        "name": "John Doe",
                        "email": "john@company.com",
                        "role": "Employee",
                        "team": "Engineering",
                        "is_active": True
                    }
                ],
                "total": 1
            }
        }


class UserCreateResponse(BaseModel):
    message: str
    user: UserResponse

    class Config:
        json_schema_extra = {
            "example": {
                "message": "User created successfully",
                "user": {
                    "id": "user-1",
                    "name": "John Doe",
                    "email": "john@company.com",
                    "role": "Employee",
                    "team": "Engineering",
                    "is_active": True
                }
            }
        }

class MealInfo(BaseModel):
    meal_type: MealType
    is_participating: bool
    can_edit: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "meal_type": "lunch",
                "is_participating": True,
                "can_edit": True
            }
        }

# ===========================
# Meal Participation Schemas (used by meals router)
# ===========================

class MealParticipationResponse(BaseModel):
    id: str
    user_id: str
    meal_type: str
    date: str
    is_participating: bool
    updated_by: str | None = None
    updated_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "part-001",
                "user_id": "user-1",
                "meal_type": "lunch",
                "date": "2026-02-17",
                "is_participating": True,
                "updated_by": "user-1",
                "updated_at": "2026-02-17T10:30:00"
            }
        }

class UserMealsResponse(BaseModel):
    date: str
    meals: List[MealParticipationResponse]
    cutoff_passed: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-02-17",
                "meals": [
                    {
                        "id": "part-001",
                        "user_id": "user-1",
                        "meal_type": "lunch",
                        "date": "2026-02-17",
                        "is_participating": True,
                        "updated_by": "user-1",
                        "updated_at": "2026-02-17T10:30:00"
                    }
                ],
                "cutoff_passed": False
            }
        }

class TodayMealsResponse(BaseModel):
    """Simplified today meals response using MealInfo."""
    date: date
    meals: list[MealInfo]

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2023-01-15",
                "meals": [
                    {
                        "meal_type": "lunch",
                        "is_participating": True,
                        "can_edit": True
                    },
                    {
                        "meal_type": "snacks",
                        "is_participating": False,
                        "can_edit": False
                    }
                ]
                
            }
        }

class UpdateParticipationRequest(BaseModel):
    is_participating: bool

    class Config:
        json_schema_extra = {
            "example": {
                "is_participating": True
            }
        }

class ParticipationUpdateRequest(BaseModel):
    meal_type: MealType
    is_participating: bool

    class Config:
        json_schema_extra = {
            "example": {
                "meal_type": "lunch",
                "is_participating": True
            }
        }

class ParticipationDetail(BaseModel):
    meal_type: MealType
    is_participating: bool
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "meal_type": "lunch",
                "is_participating": True,
                "updated_at": "2026-01-15T12:00:00Z"
            }
        }

class ParticipationUpdateResponse(BaseModel):
    message: str
    participation: ParticipationDetail

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Participation updated successfully",
                "participation": {
                    "meal_type": "lunch",
                    "is_participating": True,
                    "updated_at": "2026-01-15T12:00:00Z"
            }     
        }
    }

class AdminParticipationOverrideRequest(BaseModel):
    user_id: str
    meal_type: str
    is_participating: bool

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-1",
                "meal_type": "lunch",
                "is_participating": False
            }
        }


# ===========================
# Batch Participation Schemas
# ===========================

class BatchParticipationItem(BaseModel):
    """A single participation change within a batch request."""
    user_id: str
    meal_type: str
    is_participating: bool

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-1",
                "meal_type": "lunch",
                "is_participating": False
            }
        }


class BatchParticipationRequest(BaseModel):
    """Wraps a list of updates so the frontend can send one request."""
    updates: List[BatchParticipationItem]

    class Config:
        json_schema_extra = {
            "example": {
                "updates": [
                    {"user_id": "user-1", "meal_type": "lunch", "is_participating": False},
                    {"user_id": "user-1", "meal_type": "snacks", "is_participating": False}
                ]
            }
        }


class BatchParticipationResultItem(BaseModel):
    user_id: str
    meal_type: str
    success: bool
    message: str


class BatchParticipationResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: List[BatchParticipationResultItem]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "succeeded": 2,
                "failed": 0,
                "results": [
                    {"user_id": "user-1", "meal_type": "lunch", "success": True, "message": "Updated"},
                    {"user_id": "user-1", "meal_type": "snacks", "success": True, "message": "Updated"}
                ]
            }
        }


# ===========================
# Bulk Participation Schemas (FR-8)
# ===========================

class BulkParticipationRequest(BaseModel):
    """Bulk-update meals for multiple users on a specific date."""
    user_ids: List[str]
    date: date
    meals: Dict[str, bool]  
    reason: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_ids": ["user-1", "user-2"],
                "date": "2026-02-20",
                "meals": {"lunch": True, "snacks": False},
                "reason": "Team outing"
            }
        }


class BulkParticipationResponse(BaseModel):
    updated_count: int
    failed: List[Dict[str, str]]
    date: str

    class Config:
        json_schema_extra = {
            "example": {
                "updated_count": 4,
                "failed": [{"user_id": "user-3", "error": "User not found"}],
                "date": "2026-02-20"
            }
        }


# ===========================
# Exception Participation Schema (FR-8)
# ===========================

class ExceptionParticipationRequest(BaseModel):
    """Team Lead overrides a single user's meal participation with a reason."""
    user_id: str
    date: date
    meal_type: str
    is_participating: bool
    reason: str

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-1",
                "date": "2026-02-20",
                "meal_type": "lunch",
                "is_participating": False,
                "reason": "Working from home"
            }
        }

class AdminParticipationUpdateResponse(BaseModel):
    message: str
    user_name: str
    participation: ParticipationDetail

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Participation updated for user",
                "user_name": "John Doe",
                "participation": {
                    "meal_type": "lunch",
                    "is_participating": False,
                    "updated_at": "2026-02-06T10:30:00"
                }
            }
        }

# ===========================
# Meal Configuration Schemas
# ===========================

class MealConfigResponse(BaseModel):
    enabled_meals: Dict[str, bool]

    class Config:
        json_schema_extra = {
            "example": {
                "enabled_meals": {
                    "lunch": True,
                    "snacks": True,
                    "iftar": False,
                    "event_dinner": False,
                    "optional_dinner": True
                }
            }
        }

class MealConfigUpdateRequest(BaseModel):
    meal_type: str
    enabled: bool

    class Config:
        json_schema_extra = {
            "example": {
                "meal_type": "iftar",
                "enabled": True
            }
        }

# ===========================
# Headcount Schemas
# ===========================

class HeadcountResponse(BaseModel):
    date: str
    headcount: Dict[str, int]
    total_employees: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-02-06",
                "headcount": {
                    "lunch": 87,
                    "snacks": 92,
                    "iftar": 45,
                    "event_dinner": 0,
                    "optional_dinner": 12
                },
                "total_employees": 100
            }
        }


class MessageResponse(BaseModel):
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully"
            }
        }


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid credentials",
                "error_code": "AUTH_ERROR",
                "timestamp": "2026-02-06T10:30:00"
            }
        }


# ===========================
# Work Location Schemas
# ===========================

class WorkLocationUpdate(BaseModel):
    """Request to set a user's work location for a date."""
    date: date
    location: WorkLocationType

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-02-19",
                "location": "Office"
            }
        }


class AdminWorkLocationUpdate(BaseModel):
    """Admin request to set any user's work location."""
    user_id: str
    date: date
    location: WorkLocationType

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-1",
                "date": "2026-02-19",
                "location": "WFH"
            }
        }


class WorkLocationResponse(BaseModel):
    id: str
    user_id: str
    date: str
    location: str
    updated_by: Optional[str] = None
    updated_at: str

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


class WorkLocationListResponse(BaseModel):
    date: str
    locations: List[WorkLocationResponse]
    total: int


# ===========================
# Team Participation Schemas
# ===========================

class TeamMemberParticipation(BaseModel):
    user_id: str
    user_name: str
    email: str
    work_location: str = "Office"
    meals: Dict[str, bool] = {}


class TeamParticipationResponse(BaseModel):
    team: str
    date: str
    members: List[TeamMemberParticipation]
    total_members: int

    class Config:
        json_schema_extra = {
            "example": {
                "team": "Engineering",
                "date": "2026-02-19",
                "members": [
                    {
                        "user_id": "user-1",
                        "user_name": "John Doe",
                        "email": "john@company.com",
                        "work_location": "Office",
                        "meals": {"lunch": True, "snacks": False}
                    }
                ],
                "total_members": 1
            }
        }

# ===========================
# Special Day Schemas
# ===========================

class SpecialDayCreate(BaseModel):
    #Request to create a special day.
    date: date
    day_type: DayType
    note: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-03-26",
                "day_type": "governmentholiday",
                "note": "Independence Day"
            }
        }


class SpecialDayResponse(BaseModel):
    id: str
    date: str
    day_type: str
    note: Optional[str] = None
    created_by: str
    created_at: str

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


class SpecialDayListResponse(BaseModel):
    special_days: List[SpecialDayResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "special_days": [
                    {
                        "id": "sd-001",
                        "date": "2026-03-26",
                        "day_type": "governmentholiday",
                        "note": "Independence Day",
                        "created_by": "admin-user-id",
                        "created_at": "2026-02-19T10:30:00"
                    }
                ],
                "total": 1
            }
        }