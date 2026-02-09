from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas import LoginRequest, LoginResponse, UserRegister, UserResponse
from app.models import User, UserRole
from app import auth as auth_service
from app import storage

router = APIRouter()

# ===========================
# Login Endpoint
# ===========================

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint - authenticate user with email and password
    Returns: Access token and user information
    """
    user = auth_service.authenticate_user(request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return auth_service.create_token_response(user)

# ===========================
# Register Endpoint
# ===========================

@router.post("/register", response_model=LoginResponse)
async def register(request: UserRegister):
    """
    Register endpoint - create a new employee account
    Returns: Access token and user information
    """
    # Check if user already exists
    existing_user = storage.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_valid, error_message = auth_service.validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Hash password and create user
    password_hash = auth_service.hash_password(request.password)
    
    new_user = User(
        name=request.name,
        email=request.email,
        password_hash=password_hash,
        role=UserRole.EMPLOYEE,
        department=request.department,
        is_active=True
    )
    
    # Save user to storage
    created_user = storage.create_user(new_user)
    
    # Log authentication attempt
    auth_service.log_authentication_attempt(request.email, True)
    
    return auth_service.create_token_response(created_user)

# ===========================
# Get Current User Endpoint
# ===========================

@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(auth_service.get_current_user)):
    """
    Get current authenticated user information
    """
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        department=current_user.department,
        is_active=current_user.is_active
    )
