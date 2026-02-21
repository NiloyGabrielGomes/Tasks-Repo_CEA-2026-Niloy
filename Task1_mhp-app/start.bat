@echo off
start "Backend" cmd /k "cd backend && python run.py"
start "Frontend" cmd /k "cd frontend && npm run dev"
echo.
echo Application started!
echo Frontend: http://localhost:5173
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
