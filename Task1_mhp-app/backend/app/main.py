from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    version="1.0.0"
)

# ===========================
# CORS Middleware
# ===========================

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
    return {
        "status": "ok",
        "message": "Meal Headcount Planner API is running"
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
        "openapi": "/openapi.json"
    }

# ===========================
# Startup Event
# ===========================

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    print("🚀 Starting Meal Headcount Planner API...")
    storage.seed_initial_data()
    print("✅ API started successfully")

# ===========================
# Shutdown Event
# ===========================

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down Meal Headcount Planner API...")
