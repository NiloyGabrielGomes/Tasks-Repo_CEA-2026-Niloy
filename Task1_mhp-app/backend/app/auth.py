import os
import secrets
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

from app.models import User, UserRole
from app import storage
from app.storage import get_user_by_email

load_dotenv()

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in environment variables")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# ===========================
# SSE One-Time Token Store
# ===========================
# Short-lived tokens (60 s) issued to authenticated users before they open an
# EventSource connection.  Each token is single-use: it is marked "used" the
# moment the SSE endpoint consumes it, preventing replay attacks.

SSE_TOKEN_EXPIRE_SECONDS = 60  # keep small so leaked tokens are useless

_sse_lock  = threading.Lock()
_sse_store: dict[str, dict] = {}  


def _cleanup_sse_store() -> None:
    now = datetime.utcnow()
    stale = [k for k, v in _sse_store.items() if v["expires_at"] < now]
    for k in stale:
        del _sse_store[k]

# Using pbkdf2_sha256 due to bcrpypt compatibility issues.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

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
# Consolidated role-based dependency (replace require_* functions with require_role)
# ===========================

def require_role(allowed_roles: list):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            allowed = ', '.join(r.value for r in allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {allowed}. Your role: {current_user.role.value}",
            )
        return current_user
    return role_checker


require_employee = require_role([UserRole.EMPLOYEE, UserRole.TEAM_LEAD, UserRole.ADMIN])
require_team_lead = require_role([UserRole.TEAM_LEAD, UserRole.ADMIN])
require_admin = require_role([UserRole.ADMIN])


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
# SSE Short-Lived Token API
# ===========================

def create_sse_token(user: User) -> dict:
    """
    Issue a short-lived (SSE_TOKEN_EXPIRE_SECONDS), single-use JWT for the
    SSE stream endpoint.  Returns {"token": <str>, "expires_in": <int>}.
    """
    expires_at = datetime.utcnow() + timedelta(seconds=SSE_TOKEN_EXPIRE_SECONDS)
    jti = secrets.token_hex(16)          # unique nonce for revocation tracking

    payload = {
        "sub": user.email,
        "type": "sse",
        "jti": jti,
        "exp": expires_at,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    with _sse_lock:
        _cleanup_sse_store()
        _sse_store[jti] = {
            "email": user.email,
            "expires_at": expires_at,
            "used": False,
        }

    logger.info("SSE token issued for user %s (jti=%s)", user.email, jti)
    return {"token": token, "expires_in": SSE_TOKEN_EXPIRE_SECONDS}


def validate_and_consume_sse_token(token: str) -> Optional[User]:
    # ── JWT decode ──────────────────────────────────────────────
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        logger.warning("SSE token validation failed — JWT error: %s", exc)
        return None

    # ── Claim checks ────────────────────────────────────────────
    if payload.get("type") != "sse":
        logger.warning("SSE token validation failed — not flagged as SSE token")
        return None

    jti: Optional[str] = payload.get("jti")
    email: Optional[str] = payload.get("sub")

    if not jti or not email:
        logger.warning("SSE token validation failed — missing jti or sub claim")
        return None

    # ── Revocation store ────────────────────────────────────────
    with _sse_lock:
        entry = _sse_store.get(jti)

        if entry is None:
            logger.warning(
                "SSE token validation failed — jti %r not found (expired or never issued)", jti
            )
            return None

        if entry["used"]:
            logger.warning(
                "SSE token validation failed — jti %r already consumed (replay attempt by %s)", jti, email
            )
            return None

        if entry["expires_at"] < datetime.utcnow():
            logger.warning(
                "SSE token validation failed — jti %r is expired (store clock check)", jti
            )
            del _sse_store[jti]
            return None

        # Consume — mark used so no second connection can reuse this token
        entry["used"] = True

    # ── User lookup ─────────────────────────────────────────────
    user = storage.get_user_by_email(email)
    if user is None:
        logger.warning("SSE token validation failed — user %r not found", email)
        return None

    if not user.is_active:
        logger.warning("SSE token validation failed — user %r is inactive", email)
        return None

    logger.info("SSE token consumed for user %s (jti=%s)", email, jti)
    return user


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