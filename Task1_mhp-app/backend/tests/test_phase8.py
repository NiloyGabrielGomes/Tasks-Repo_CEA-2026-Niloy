"""
Phase 8 — Tests for Event Meals, Audit Logs, and Policy Config endpoints.

Uses the in-memory SQLite fixture from conftest.py (test_db yields an engine).
Follows the same patterns as test_e2e_smoke.py.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.models import User, UserRole
from app.auth import hash_password


# ── TestClient ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ── User / token helpers ──────────────────────────────────────────────────────

def _create_user(engine, email: str, password: str, role: UserRole, name: str, team: str | None = None) -> User:
    """Insert a user directly into the test DB."""
    user = User(
        email=email,
        name=name,
        password_hash=hash_password(password),
        role=role,
        team=team,
        is_active=True,
    )
    with Session(engine) as sess:
        sess.add(user)
        sess.commit()
        sess.refresh(user)
    return user


def _login(client, email: str, password: str) -> str:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Event Meals Tests ─────────────────────────────────────────────────────────

class TestEventMeals:

    def test_create_event_meal_as_admin(self, client, test_db):
        """Admin can create an event meal."""
        _create_user(test_db, "evtadmin@test.com", "pass1234", UserRole.ADMIN, "Evt Admin")
        token = _login(client, "evtadmin@test.com", "pass1234")

        data = {
            "date": "2026-03-10",
            "meal_type": "event_dinner",
            "note": "Company Anniversary Dinner",
        }
        r = client.post("/api/event_meals/", json=data, headers=_auth(token))
        assert r.status_code == 201, f"Create failed: {r.status_code} {r.text}"
        body = r.json()
        assert body["date"] == "2026-03-10"
        assert body["meal_type"] == "event_dinner"
        assert body["note"] == "Company Anniversary Dinner"
        assert "id" in body

    def test_create_event_meal_as_employee_forbidden(self, client, test_db):
        """Employee cannot create event meals (403)."""
        _create_user(test_db, "evtemp@test.com", "pass1234", UserRole.EMPLOYEE, "Evt Emp")
        token = _login(client, "evtemp@test.com", "pass1234")

        data = {
            "date": "2026-03-10",
            "meal_type": "event_dinner",
            "note": "Should fail",
        }
        r = client.post("/api/event_meals/", json=data, headers=_auth(token))
        assert r.status_code == 403

    def test_list_event_meals(self, client, test_db):
        """Admin can list event meals."""
        _create_user(test_db, "evtlist@test.com", "pass1234", UserRole.ADMIN, "Evt List")
        token = _login(client, "evtlist@test.com", "pass1234")

        # Create one first
        client.post(
            "/api/event_meals/",
            json={"date": "2026-04-01", "meal_type": "lunch", "note": "Test"},
            headers=_auth(token),
        )

        r = client.get("/api/event_meals/", headers=_auth(token))
        assert r.status_code == 200
        body = r.json()
        assert "event_meals" in body
        assert "total" in body
        assert body["total"] >= 1

    def test_delete_event_meal(self, client, test_db):
        """Admin can delete an event meal."""
        _create_user(test_db, "evtdel@test.com", "pass1234", UserRole.ADMIN, "Evt Del")
        token = _login(client, "evtdel@test.com", "pass1234")

        r = client.post(
            "/api/event_meals/",
            json={"date": "2026-05-01", "meal_type": "snacks", "note": "deleteme"},
            headers=_auth(token),
        )
        evt_id = r.json()["id"]

        r2 = client.delete(f"/api/event_meals/{evt_id}", headers=_auth(token))
        assert r2.status_code == 200
        assert "message" in r2.json()

    def test_get_today_event_meals_employee_ok(self, client, test_db):
        """Employee can view today's event meals."""
        _create_user(test_db, "evttodayemp@test.com", "pass1234", UserRole.EMPLOYEE, "Today Emp")
        token = _login(client, "evttodayemp@test.com", "pass1234")

        r = client.get("/api/event_meals/today", headers=_auth(token))
        assert r.status_code == 200
        body = r.json()
        assert "event_meals" in body


# ── Audit Logs Tests ──────────────────────────────────────────────────────────

class TestAuditLogs:

    def test_list_audit_logs_as_admin(self, client, test_db):
        """Admin can view audit logs."""
        _create_user(test_db, "auditadm@test.com", "pass1234", UserRole.ADMIN, "Audit Admin")
        token = _login(client, "auditadm@test.com", "pass1234")

        r = client.get("/api/audit_logs/", headers=_auth(token))
        assert r.status_code == 200
        body = r.json()
        assert "audit_logs" in body
        assert "total" in body
        assert body["total"] >= 0

    def test_list_audit_logs_as_employee_forbidden(self, client, test_db):
        """Employee cannot view audit logs (403)."""
        _create_user(test_db, "auditemp@test.com", "pass1234", UserRole.EMPLOYEE, "Audit Emp")
        token = _login(client, "auditemp@test.com", "pass1234")

        r = client.get("/api/audit_logs/", headers=_auth(token))
        assert r.status_code == 403


# ── Policy Config Tests ───────────────────────────────────────────────────────

class TestPolicyConfig:

    def test_get_policy_config_as_admin(self, client, test_db):
        """Admin can view policy config."""
        _create_user(test_db, "polget@test.com", "pass1234", UserRole.ADMIN, "Pol Admin")
        token = _login(client, "polget@test.com", "pass1234")

        r = client.get("/api/policy/", headers=_auth(token))
        assert r.status_code == 200
        body = r.json()
        assert "cutoff_time" in body
        assert "forward_planning_days" in body

    def test_update_policy_config_as_admin(self, client, test_db):
        """Admin can update policy config."""
        _create_user(test_db, "polupd@test.com", "pass1234", UserRole.ADMIN, "Pol Updater")
        token = _login(client, "polupd@test.com", "pass1234")

        data = {"cutoff_time": "20:00"}
        r = client.put("/api/policy/", json=data, headers=_auth(token))
        assert r.status_code == 200
        body = r.json()
        assert body["cutoff_time"] == "20:00"

    def test_update_policy_config_as_employee_forbidden(self, client, test_db):
        """Employee cannot update policy config (403)."""
        _create_user(test_db, "polemp@test.com", "pass1234", UserRole.EMPLOYEE, "Pol Emp")
        token = _login(client, "polemp@test.com", "pass1234")

        data = {"cutoff_time": "20:00"}
        r = client.put("/api/policy/", json=data, headers=_auth(token))
        assert r.status_code == 403

    def test_get_policy_config_as_employee(self, client, test_db):
        """Employee can also view policy config (read-only)."""
        _create_user(test_db, "polempr@test.com", "pass1234", UserRole.EMPLOYEE, "Pol Reader")
        token = _login(client, "polempr@test.com", "pass1234")

        r = client.get("/api/policy/", headers=_auth(token))
        assert r.status_code == 200
        assert "cutoff_time" in r.json()
