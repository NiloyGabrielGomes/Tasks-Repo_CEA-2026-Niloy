from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas import UserResponse, UserListResponse, UserUpdate
from app.models import User, UserRole
from app import auth as auth_service
from app import storage

router = APIRouter()

# ===========================
# Get All Users
# ===========================

@router.get("", response_model=UserListResponse)
async def get_all_users(current_user: User = Depends(auth_service.require_admin)):
    """
    Get list of all users - Admin only
    """
    all_users = storage.get_all_users()
    user_responses = [
        UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            department=user.department,
            is_active=user.is_active
        )
        for user in all_users
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
        department=user.department,
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
    if update_data.department is not None:
        user.department = update_data.department
    if update_data.is_active is not None:
        user.is_active = update_data.is_active
    
    # Save updated user
    updated_user = storage.update_user(user)
    
    return UserResponse(
        id=updated_user.id,
        name=updated_user.name,
        email=updated_user.email,
        role=updated_user.role,
        department=updated_user.department,
        is_active=updated_user.is_active
    )

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
        department=current_user.department,
        is_active=current_user.is_active
    )
