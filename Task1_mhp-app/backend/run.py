#!/usr/bin/env python
"""
Startup script for the Meal Headcount Planner API
Run with: python run.py
"""

import uvicorn
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    print("🚀 Starting Meal Headcount Planner API...")
    print("📚 API Docs: http://localhost:8000/docs")
    print("📖 OpenAPI JSON: http://localhost:8000/openapi.json")
    print("💊 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
