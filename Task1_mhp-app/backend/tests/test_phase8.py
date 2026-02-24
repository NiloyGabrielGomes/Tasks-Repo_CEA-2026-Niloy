from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime, timedelta

from app.main import app
from app.database import get_session
from app.models import EventMeal, User, AuditLogEntry

client = TestClient(app)

# Helper function to get an admin token
def get_admin_token(test_db: Session) -> str:
    # Get the admin user from db (seeded by seed_db)
    admin_user = test_db.exec(select(User).where(User.email == "admin@mhp.com")).first()
    response = client.post("/api/auth/token", auth=(admin_user.email, "admin123"))
    return response.json()["access_token"]

# Helper function to get an employee token
def get_emp_token(test_db: Session) -> str:
    # Get employee user
    emp_user = test_db.exec(select(User).where(User.email == "emp1@mhp.com")).first()
    response = client.post("/api/auth/token", auth=(emp_user.email, "emp123"))
    return response.json()["access_token"]


def test_create_event_meal_as_admin(test_db: Session):
    token = get_admin_token(test_db)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create event meal
    future_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    data = {
        "date": future_date,
        "meal_type": "event_dinner",
        "note": "Company Anniversary Dinner"
    }
    
    response = client.post("/api/event_meals/", json=data, headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["date"] == future_date
    assert res_data["meal_type"] == "event_dinner"
    assert res_data["note"] == "Company Anniversary Dinner"
    
    # Check DB
    event_meal = test_db.exec(select(EventMeal).where(EventMeal.id == res_data["id"])).first()
    assert event_meal is not None
    assert event_meal.date == future_date
    
    # Check Audit Log
    logs = test_db.exec(select(AuditLog).where(AuditLog.action == "CREATE_EVENT_MEAL")).all()
    assert len(logs) > 0
    assert "Company Anniversary Dinner" in logs[-1].details

def test_create_event_meal_as_employee_fails(test_db: Session):
    token = get_emp_token(test_db)
    headers = {"Authorization": f"Bearer {token}"}
    
    future_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    data = {
        "date": future_date,
        "meal_type": "event_dinner",
        "note": "Company Anniversary Dinner"
    }
    
    response = client.post("/api/event_meals/", json=data, headers=headers)
    assert response.status_code == 403


def test_list_event_meals(test_db: Session):
    token = get_admin_token(test_db)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/event_meals/", headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert isinstance(res_data, list)


def test_list_audit_logs_as_admin(test_db: Session):
    token = get_admin_token(test_db)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/audit_logs/", headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert "items" in res_data
    assert "total_count" in res_data
    assert res_data["total_count"] >= 0

def test_list_audit_logs_as_employee_fails(test_db: Session):
    token = get_emp_token(test_db)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/audit_logs/", headers=headers)
    assert response.status_code == 403

def test_update_policy_config_as_admin(test_db: Session):
    token = get_admin_token(test_db)
    headers = {"Authorization": f"Bearer {token}"}
    
    # View policy
    res1 = client.get("/api/policy/", headers=headers)
    assert res1.status_code == 200
    
    # Update policy
    data = {"cutoff_time": "20:00"}
    res2 = client.put("/api/policy/", json=data, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["cutoff_time"] == "20:00"

def test_update_policy_config_as_emp_fails(test_db: Session):
    token = get_emp_token(test_db)
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {"cutoff_time": "20:00"}
    response = client.put("/api/policy/", json=data, headers=headers)
    assert response.status_code == 403
