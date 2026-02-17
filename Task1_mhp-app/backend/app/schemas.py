from datetime import datetime, date
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, EmailStr
from app.models import UserRole, MealType

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