from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from dotenv import load_dotenv

from app.routers import auth, users, meals
from app import storage

load_dotenv()

# ===========================
# FastAPI App Setup
# ===========================

app = FastAPI(
    title="Meal Headcount Planner API",
    description="API for managing daily meal participation tracking",
    version="1.0.0",
    contact={
        "name": "MHP Support",
        "email": "none@company.com"
    }
)

# ===========================
# CORS Middleware
# ===========================

frontend_url = os.getenv("frontend_url", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_url,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================
# Route Includes
# ===========================

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(meals.router, prefix="/api/meals", tags=["Meals"])

# ===========================
# Health Check Endpoint
# ===========================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify API is running"""
    from app import storage

    try:
        users = storage.get_all_users()
        user_count = len(users)
        storage_status = "ok"

    except Exception as e:
        user_count = 0
        storage_status = f"error: {str(e)}"
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "message": "Meal Headcount Planner API is running",
        "checks": {
            "api": "ok",
            "storage": storage_status,
            "user_count": user_count
        }
    }

# ===========================
# Root Endpoint
# ===========================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "api": "Meal Headcount Planner API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "redoc": "/redoc",
        "health": "/health",
        "api_base": "/api"
    }

# ===========================
# Startup Event
# ===========================

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    print("=" * 60)
    print("🚀 Starting Meal Headcount Planner API...")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Frontend URL: {frontend_url}")
    print(f" API Docs: http://localhost:8000/docs")
    print(f" Health Check: http://localhost:8000/health")
    print("=" * 60)
    storage.seed_initial_data()
    from app import storage
    users = storage.get_all_users()
    
    if not users:
        print("⚠️  No users found in database!")
        print("💡 Run: python -m app.storage")
        print("   to create seed data with test users")
        print("=" * 60)
    else:
        print(f"✓ Found {len(users)} users in database")
        print("=" * 60)
    print("✅ API started successfully")

# ===========================
# Shutdown Event
# ===========================

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down Meal Headcount Planner API...")

# ===========================
# API Info Endpoint
# ===========================

@app.get("/api", tags=["Info"])
async def api_info():
    return{
        "name": "Meal Headcount Planner API",
        "version": "0.1.0",
        "endpoints": {
            "authentication": {
                "login": "POST /api/auth/login",
                "register": "POST /api/users/register"
            },
            "users": {
                "me": "GET /api/users/me",
                "create": "POST /api/users/create (Admin)",
                "list": "GET /api/users (Admin)",
                "get": "GET /api/users/{user_id} (TeamLead/Admin)",
                "update": "PUT /api/users/{user_id} (Admin)",
                "delete": "DELETE /api/users/{user_id} (Admin)"
            },
            "meals": {
                "today": "GET /api/meals/today",
                "update": "PUT /api/meals/participation",
                "admin_update": "POST /api/meals/participation/admin (TeamLead/Admin)",
                "headcount": "GET /api/meals/headcount/today (Admin)"
            }
        }
    }

# ===========================
# Router Registration
# ===========================

app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    users.router,
    prefix="/api/users",
    tags=["Users"]
)

app.include_router(
    meals.router,
    prefix="/api/meals",
    tags=["Meals"]
)

# ===========================
# Exception Handlers
# ===========================

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": exc.errors(),
            "body": exc.body
        }
    )

@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "error_code": "VALUE_ERROR"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    import traceback
    
    # Log the full error (in production, use proper logging)
    print("=" * 60)
    print("Unexpected Error:")
    print(traceback.format_exc())
    print("=" * 60)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# ===========================
# Development Mode Configuration
# ===========================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )