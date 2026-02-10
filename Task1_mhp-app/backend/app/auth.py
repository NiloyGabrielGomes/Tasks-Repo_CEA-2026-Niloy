import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

from app.models import User, UserRole
from app import storage

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in environment variables")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBearer()


# ===========================
# Password Functions
# ===========================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ===========================
# JWT Token Functions
# ===========================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Encode token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ===========================
# Authentication Functions
# ===========================

def authenticate_user(email: str, password: str) -> Optional[User]:
    user = storage.get_user_by_email(email)
    if not user:
        return None
    
    if not user.is_active:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user


# ===========================
# Token Dependency Functions
# ===========================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception 
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception   
    user = storage.get_user_by_email(email)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user


# ===========================
# Role-Based Access Control Dependencies
# ===========================

async def require_employee(current_user: User = Depends(get_current_user)) -> User:
    return current_user


async def require_team_lead(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRole.TEAM_LEAD, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team Lead or Admin access required"
        )
    return current_user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ===========================
# Helper Functions
# ===========================

def create_token_response(user: User) -> dict:
    access_token_data = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.role.value
    }
    
    access_token = create_access_token(access_token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "team": user.team,
            "is_active": user.is_active
        }
    }


def get_user_from_token(token: str) -> Optional[User]:
    payload = verify_token(token)
    if not payload:
        return None
    
    email = payload.get("sub")
    if not email:
        return None
    
    return storage.get_user_by_email(email)


# ===========================
# Token Validation Utilities
# ===========================

def is_token_expired(token: str) -> bool:
    payload = verify_token(token)
    if not payload:
        return True
    
    exp = payload.get("exp")
    if not exp:
        return True
    
    return datetime.utcnow().timestamp() > exp


def get_token_expiry(token: str) -> Optional[datetime]:
    payload = verify_token(token)
    if not payload:
        return None
    
    exp = payload.get("exp")
    if not exp:
        return None
    
    return datetime.utcfromtimestamp(exp)


# ===========================
# Security Audit Functions
# ===========================

def log_authentication_attempt(email: str, success: bool, ip_address: str = None):
    import logging
    
    logger = logging.getLogger(__name__)
    
    status = "SUCCESS" if success else "FAILED"
    log_message = f"Login {status} for {email}"
    
    if ip_address:
        log_message += f" from {ip_address}"
    
    if success:
        logger.info(log_message)
    else:
        logger.warning(log_message)


# ===========================
# Password Strength Validation
# ===========================

def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    # Future: Add complexity requirements here
    # if not any(c.isupper() for c in password):
    #     return False, "Password must contain at least one uppercase letter"
    # if not any(c.isdigit() for c in password):
    #     return False, "Password must contain at least one number"
    
    return True, ""


# ===========================
# Testing Utilities
# ===========================

if __name__ == "__main__":

    print("Testing Authentication Module")
    print("=" * 50)
    
    print("\n1. Testing password hashing...")
    password = "test_password_123"
    hashed = hash_password(password)
    print(f"   Original: {password}")
    print(f"   Hashed: {hashed[:50]}...")
    print(f"   Verification: {verify_password(password, hashed)}")
    assert verify_password(password, hashed), "Password verification failed!"
    print("   ✓ Password hashing works")
    
    print("\n2. Testing JWT token...")
    token_data = {
        "sub": "test@test.com",
        "user_id": "test-123",
        "role": "Employee"
    }
    token = create_access_token(token_data)
    print(f"   Token: {token[:50]}...")
    
    payload = verify_token(token)
    print(f"   Decoded: {payload}")
    assert payload["sub"] == "test@test.com", "Token verification failed!"
    print("   ✓ JWT token works")
    
    print("\n3. Testing password strength validation...")
    valid, error = validate_password_strength("short")
    print(f"   'short': Valid={valid}, Error='{error}'")
    assert not valid, "Short password should be invalid"
    
    valid, error = validate_password_strength("long_enough_password")
    print(f"   'long_enough_password': Valid={valid}, Error='{error}'")
    assert valid, "Long password should be valid"
    print("   ✓ Password validation works")
    
    print("\n4. Testing token expiry...")
    token = create_access_token({"sub": "test@test.com"})
    expired = is_token_expired(token)
    print(f"   Token expired: {expired}")
    assert not expired, "Fresh token should not be expired"
    
    expiry = get_token_expiry(token)
    print(f"   Token expires at: {expiry}")
    print("   ✓ Token expiry check works")
    
    print("\n" + "=" * 50)
    print("All authentication tests passed! ✓")