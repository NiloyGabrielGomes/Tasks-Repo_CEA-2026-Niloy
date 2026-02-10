from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas import UserResponse, UserListResponse, UserUpdate, UserCreate
from app.models import User, UserRole
from app import auth as auth_service
from app import storage

router = APIRouter()

# ===========================
# Get All Users
# ===========================

@router.get("", response_model=UserListResponse)
async def get_all_users(current_user: User = Depends(auth_service.require_team_lead)):
    """
    Get list of all users - Team Lead and Admin
    """
    all_users = storage.get_all_users()
    user_responses = [
        UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            team=user.team,
            is_active=user.is_active
        )
        for user in all_users
    ]
    
    return UserListResponse(users=user_responses, total=len(user_responses))

# ===========================
# Admin Create User
# ===========================

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    user_data: UserCreate,
    current_user: User = Depends(auth_service.require_admin)
):
    """
    Create a new user with any role - Admin only
    """
    existing = storage.get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    password_hash = auth_service.hash_password(user_data.password)
    
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash,
        role=user_data.role,
        team=user_data.team,
        is_active=True
    )
    
    try:
        created_user = storage.create_user(new_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    
    return UserResponse(
        id=created_user.id,
        name=created_user.name,
        email=created_user.email,
        role=created_user.role,
        team=created_user.team,
        is_active=created_user.is_active
    )

# ===========================
# Get Users in My Team
# ===========================

@router.get("/team", response_model=UserListResponse)
async def get_team_users(current_user: User = Depends(auth_service.require_team_lead)):
    """
    Get list of users in the current user's team - Team Lead and Admin
    """
    team_users = storage.get_users_by_team(current_user.team)
    user_responses = [
        UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            team=user.team,
            is_active=user.is_active
        )
        for user in team_users
    ]
    
    return UserListResponse(users=user_responses, total=len(user_responses))

# ===========================
# Get User by ID
# ===========================

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: User = Depends(auth_service.get_current_user)):
    """
    Get user by ID - User can view own profile, admin can view any
    """
    # Check permissions
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this user"
        )
    
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        team=user.team,
        is_active=user.is_active
    )

# ===========================
# Update User
# ===========================

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: User = Depends(auth_service.require_admin)
):
    """
    Update user information - Admin only
    """
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if update_data.name is not None:
        user.name = update_data.name
    if update_data.role is not None:
        user.role = update_data.role
    if update_data.team is not None:
        user.team = update_data.team
    if update_data.is_active is not None:
        user.is_active = update_data.is_active
    
    # Save updated user
    updated_user = storage.update_user(user)
    
    return UserResponse(
        id=updated_user.id,
        name=updated_user.name,
        email=updated_user.email,
        role=updated_user.role,
        team=updated_user.team,
        is_active=updated_user.is_active
    )

# ===========================
# Deactivate User (Soft Delete)
# ===========================

@router.delete("/{user_id}")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(auth_service.require_admin)
):
    """
    Soft delete - deactivate a user. Admin only.
    """
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = False
    storage.update_user(user)
    
    return {"message": f"User {user.name} has been deactivated"}

# ===========================
# Get Current User Profile
# ===========================

@router.get("/profile/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(auth_service.get_current_user)):
    """
    Get current user's own profile information
    """
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        team=current_user.team,
        is_active=current_user.is_active
    )
