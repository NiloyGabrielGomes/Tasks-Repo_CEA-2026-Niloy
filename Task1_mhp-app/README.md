# Meal Headcount Planner (MHP)

A lightweight web application for managing daily meal participation tracking for 100+ employees.

## Tech Stack
- **Backend:** Python + FastAPI
- **Frontend:** React + Vite
- **Storage:** JSON files
- **Auth:** JWT tokens

## Project Status
🚧 **In Development** - Iteration 1

## Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or pnpm

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Features (Iteration 1)
- ✅ User authentication with role-based access
- ✅ Daily meal opt-in/out for employees
- ✅ Admin/Team Lead can update participation on behalf of employees
- ✅ Real-time headcount view for logistics/admin

## Project Structure

Task1_mhp-app
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   └── storage.py
│   ├── data/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env.example
└── README.md