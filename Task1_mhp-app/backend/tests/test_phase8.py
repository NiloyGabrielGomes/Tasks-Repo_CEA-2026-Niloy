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

class TestFeature4ForwardWindowAndCutoff:
    def test_forward_window_bounds(self, client, test_db):
        """Test that date endpoints enforce forward_planning_days from PolicyConfig."""
        # 1. Create a user
        _create_user(test_db, "fw@test.com", "pass1234", UserRole.EMPLOYEE, "FW User")
        token = _login(client, "fw@test.com", "pass1234")
        user_res = client.get("/api/users/me", headers=_auth(token))
        user_id = user_res.json()["id"]

        # 2. Get policy config
        pol_res = client.get("/api/policy/", headers=_auth(token))
        forward_days = pol_res.json()["forward_planning_days"]

        # 3. Calculate an invalid future date
        import datetime
        from app import utils
        today = utils.get_today()
        invalid_date = today + datetime.timedelta(days=forward_days + 1)
        invalid_date_str = invalid_date.isoformat()

        # 4. Attempt to update participation for that invalid date
        update_res = client.put(
            f"/api/meals/{user_id}/{invalid_date_str}/lunch",
            json={"is_participating": True},
            headers=_auth(token)
        )
        assert update_res.status_code == 400
        assert "forward planning window" in update_res.json()["detail"]

    def test_dynamic_cutoff_enforcement(self, client, test_db):
        """Test that cutoff_time in PolicyConfig is respected."""
        # 1. Setup
        _create_user(test_db, "cutoff@test.com", "pass1234", UserRole.ADMIN, "Admin User")
        admin_token = _login(client, "cutoff@test.com", "pass1234")
        
        _create_user(test_db, "empcut@test.com", "pass1234", UserRole.EMPLOYEE, "Emp User")
        emp_token = _login(client, "empcut@test.com", "pass1234")
        emp_res = client.get("/api/users/me", headers=_auth(emp_token))
        emp_id = emp_res.json()["id"]

        import datetime
        from app import utils
        today_str = utils.get_today().isoformat()
        current_hour = datetime.datetime.now().hour

        # 2. Change cutoff time to be in the past (e.g., current hour - 1)
        # If current_hour is 0, we can't reliably test this today without freeze_time
        # but we can try setting it to 00:00 (which is always past unless it's exactly midnight)
        cutoff_hour = max(0, current_hour - 1)
        cutoff_time_str = f"{cutoff_hour:02d}:00"
        
        pol_update = client.put(
            "/api/policy/",
            json={"cutoff_time": cutoff_time_str, "forward_planning_days": 7, "wfh_monthly_allowance": 5},
            headers=_auth(admin_token)
        )
        assert pol_update.status_code == 200

        # 3. Try to update participation as employee for today (should be blocked)
        update_res = client.put(
            f"/api/meals/{emp_id}/{today_str}/lunch",
            json={"is_participating": True},
            headers=_auth(emp_token)
        )
        assert update_res.status_code == 403
        assert "locked after" in update_res.json()["detail"]

        # 4. Change cutoff to be in the future
        future_cutoff_hour = min(23, current_hour + 1)
        if current_hour < 23:
            future_cutoff_time_str = f"{future_cutoff_hour:02d}:00"
            pol_update2 = client.put(
                "/api/policy/",
                json={"cutoff_time": future_cutoff_time_str, "forward_planning_days": 7, "wfh_monthly_allowance": 5},
                headers=_auth(admin_token)
            )
            assert pol_update2.status_code == 200

            # Should succeed now
            update_res2 = client.put(
                f"/api/meals/{emp_id}/{today_str}/lunch",
                json={"is_participating": True},
                headers=_auth(emp_token)
            )
            assert update_res2.status_code == 200
