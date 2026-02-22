"""
F-6: Backend Unit Tests
=======================

Covers:
  6A-1/6A-2  — headcount grouping / location-split logic
  6B-1→6B-3  — announcement status transitions (draft → scheduled → sent)
  6C-1/6C-3  — WFH period overlap validation
  F-1        — SSE token generation, single-use + expiry

Run:
    cd backend
    python -m pytest tests/test_unit.py -v
"""

import time
import uuid
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_user(team="Engineering", role="employee", uid=None):
    from app.models import User, UserRole
    return User(
        id=uid or str(uuid.uuid4()),
        name="Test User",
        email=f"u{uuid.uuid4().hex[:6]}@test.com",
        password_hash="x",
        role=UserRole(role),
        team=team,
        is_active=True,
    )


def _make_participation(user_id, meal, date_val, opted_in=True):
    from app.models import MealParticipation, MealType
    return MealParticipation(
        user_id=user_id,
        meal_type=MealType(meal),
        date=date_val,
        is_participating=opted_in,
    )


def _make_work_location(user_id, date_val, location="Office"):
    from app.models import WorkLocation, WorkLocationType
    return WorkLocation(
        user_id=user_id,
        date=date_val,
        location=WorkLocationType(location),
    )


# ══════════════════════════════════════════════════════════════════════════════
# 6A — Headcount grouping logic
# ══════════════════════════════════════════════════════════════════════════════

class TestHeadcountGrouping:
    """
    Tests for _build_headcount_payload in routers/sse.py.
    Storage calls are mocked so these run without a running database.
    """

    TARGET = "2026-02-22"        # fixed date for all assertions
    MEAL   = "lunch"

    def _run(self, users, participations, work_locations, enabled=None):
        """Helper: patch storage & event_bus, then call _build_headcount_payload."""
        from app.routers.sse import _build_headcount_payload

        if enabled is None:
            enabled = {self.MEAL: True}

        with (
            patch("app.routers.sse.get_all_participation", return_value=participations),
            patch("app.routers.sse.get_all_users",         return_value=users),
            patch("app.routers.sse.get_enabled_meals",     return_value=enabled),
            patch("app.routers.sse.get_work_locations_by_date", return_value=work_locations),
            patch("app.routers.sse.get_last_change_timestamp",  return_value="ts"),
        ):
            return _build_headcount_payload(self.TARGET)

    # ── 6A-1: basic opted-in totals ─────────────────────────────────────────

    def test_total_participating_counts_unique_users(self):
        """Each opted-in user should be counted once regardless of meal count."""
        u1 = _make_user("Engineering")
        u2 = _make_user("Marketing")
        d  = date.fromisoformat(self.TARGET)

        parts = [
            _make_participation(u1.id, self.MEAL, d, opts := True),
            _make_participation(u2.id, self.MEAL, d, opts),
        ]
        result = self._run([u1, u2], parts, [])

        assert result["total_participating"] == 2
        assert result["total_users"] == 2

    def test_opted_out_not_counted_in_participating(self):
        u1 = _make_user()
        d  = date.fromisoformat(self.TARGET)
        parts = [_make_participation(u1.id, self.MEAL, d, opted_in=False)]
        result = self._run([u1], parts, [])

        assert result["total_participating"] == 0
        assert result["meals"][self.MEAL]["opted_out"] == 1
        assert result["meals"][self.MEAL]["opted_in"] == 0

    def test_meals_for_different_date_ignored(self):
        u1 = _make_user()
        wrong_date = date(2026, 1, 1)
        parts = [_make_participation(u1.id, self.MEAL, wrong_date, opted_in=True)]
        result = self._run([u1], parts, [])

        assert result["total_participating"] == 0
        assert result["meals"][self.MEAL]["opted_in"] == 0

    def test_disabled_meal_absent_from_output(self):
        u1 = _make_user()
        d  = date.fromisoformat(self.TARGET)
        # only snacks enabled; lunch record should be ignored
        parts = [_make_participation(u1.id, self.MEAL, d, opted_in=True)]
        result = self._run([u1], parts, [], enabled={"snacks": True, self.MEAL: False})

        assert self.MEAL not in result["meals"]
        assert "snacks" in result["meals"]

    # ── 6A-2: by_team and by_location splits ────────────────────────────────

    def test_by_team_grouping(self):
        eng = _make_user("Engineering")
        mkt = _make_user("Marketing")
        d   = date.fromisoformat(self.TARGET)
        parts = [
            _make_participation(eng.id, self.MEAL, d, opted_in=True),
            _make_participation(mkt.id, self.MEAL, d, opted_in=True),
        ]
        result = self._run([eng, mkt], parts, [])

        by_team = result["meals"][self.MEAL]["by_team"]
        assert by_team.get("Engineering") == 1
        assert by_team.get("Marketing")   == 1

    def test_by_location_office_wfh_split(self):
        u_office = _make_user()
        u_wfh    = _make_user()
        d = date.fromisoformat(self.TARGET)
        wls = [
            _make_work_location(u_office.id, d, "Office"),
            _make_work_location(u_wfh.id,    d, "WFH"),
        ]
        parts = [
            _make_participation(u_office.id, self.MEAL, d, opted_in=True),
            _make_participation(u_wfh.id,    self.MEAL, d, opted_in=True),
        ]
        result = self._run([u_office, u_wfh], parts, wls)

        loc = result["meals"][self.MEAL]["by_location"]
        assert loc["Office"] == 1
        assert loc["WFH"]    == 1

    def test_unknown_location_defaults_to_office(self):
        """Users without a WorkLocation record should default to 'Office'."""
        u = _make_user()
        d = date.fromisoformat(self.TARGET)
        parts = [_make_participation(u.id, self.MEAL, d, opted_in=True)]
        result = self._run([u], parts, [])   # no work_locations

        loc = result["meals"][self.MEAL]["by_location"]
        assert loc["Office"] == 1
        assert loc["WFH"]    == 0

    def test_payload_shape(self):
        result = self._run([], [], [])
        assert "date"                in result
        assert "total_users"         in result
        assert "total_participating" in result
        assert "meals"               in result
        assert "timestamp"           in result
        assert result["date"] == self.TARGET


# ══════════════════════════════════════════════════════════════════════════════
# 6B — Announcement status transitions
# ══════════════════════════════════════════════════════════════════════════════

class TestAnnouncementTransitions:
    """
    Uses the in-memory DB fixture (via conftest.py) so no HTTP server is needed.
    """

    def _admin_user(self):
        import app.storage as storage
        u = _make_user(role="admin")
        storage.create_user(u)
        return u

    def _create_draft(self, created_by_id, title="Test"):
        from app.models import Announcement, AnnouncementStatus
        import app.storage as storage

        ann = Announcement(
            title=title,
            body="Body text",
            audience="everyone",
            status=AnnouncementStatus.DRAFT,
            created_by=created_by_id,
        )
        return storage.create_announcement(ann)

    # ── 6B-1: draft creation ─────────────────────────────────────────────────

    def test_created_announcement_is_draft(self):
        from app.models import AnnouncementStatus
        u = self._admin_user()
        ann = self._create_draft(u.id)

        assert ann.id is not None
        assert ann.status == AnnouncementStatus.DRAFT
        assert ann.published_at is None

    def test_draft_appears_in_list(self):
        import app.storage as storage
        u = self._admin_user()
        self._create_draft(u.id, "Alpha")
        self._create_draft(u.id, "Beta")

        results = storage.get_announcements(created_by=u.id)
        assert len(results) == 2

    def test_draft_filter_excludes_other_statuses(self):
        from app.models import AnnouncementStatus
        import app.storage as storage
        u = self._admin_user()
        draft = self._create_draft(u.id)
        # Immediately publish one
        storage.publish_announcement(draft.id)

        drafts = storage.get_announcements(created_by=u.id, status_filter="draft")
        assert len(drafts) == 0   # no remaining drafts

    # ── 6B-2: scheduling ────────────────────────────────────────────────────

    def test_future_scheduled_at_sets_scheduled_status(self):
        from app.models import AnnouncementStatus
        import app.storage as storage

        u   = self._admin_user()
        ann = self._create_draft(u.id)
        future = datetime.utcnow() + timedelta(hours=1)

        updated = storage.publish_announcement(ann.id, scheduled_at=future)
        assert updated.status     == AnnouncementStatus.SCHEDULED
        assert updated.scheduled_at is not None
        assert updated.published_at is None

    def test_past_scheduled_at_marks_sent_immediately(self):
        from app.models import AnnouncementStatus
        import app.storage as storage

        u   = self._admin_user()
        ann = self._create_draft(u.id)
        past = datetime.utcnow() - timedelta(hours=1)

        updated = storage.publish_announcement(ann.id, scheduled_at=past)
        assert updated.status      == AnnouncementStatus.SENT
        assert updated.published_at is not None

    # ── 6B-3: publish (no schedule) ─────────────────────────────────────────

    def test_publish_without_schedule_marks_sent(self):
        from app.models import AnnouncementStatus
        import app.storage as storage

        u   = self._admin_user()
        ann = self._create_draft(u.id)

        updated = storage.publish_announcement(ann.id)
        assert updated.status      == AnnouncementStatus.SENT
        assert updated.published_at is not None

    def test_publish_idempotent_for_sent_announcement(self):
        from app.models import AnnouncementStatus
        import app.storage as storage

        u   = self._admin_user()
        ann = self._create_draft(u.id)
        first  = storage.publish_announcement(ann.id)
        second = storage.publish_announcement(ann.id)   # second call

        assert first.status  == AnnouncementStatus.SENT
        assert second.status == AnnouncementStatus.SENT

    def test_unknown_id_returns_none(self):
        import app.storage as storage
        result = storage.publish_announcement("nonexistent-id")
        assert result is None


# ══════════════════════════════════════════════════════════════════════════════
# 6C — WFH period overlap validation
# ══════════════════════════════════════════════════════════════════════════════

class TestWFHOverlap:

    def _emp(self):
        import app.storage as storage
        u = _make_user()
        storage.create_user(u)
        return u

    def _period(self, emp_id, start, end):
        from app.models import WFHPeriod
        import app.storage as storage
        p = WFHPeriod(
            employee_id=emp_id,
            start_date=start,
            end_date=end,
            created_by=emp_id,
        )
        return storage.create_wfh_period(p)

    # ── pure overlap helper ───────────────────────────────────────────────────

    def test_overlap_helper_adjacent_does_not_overlap(self):
        from app.storage import _periods_overlap
        # [Jan 1–5] and [Jan 6–10] — touching but not overlapping
        assert not _periods_overlap(date(2026,1,1), date(2026,1,5),
                                    date(2026,1,6), date(2026,1,10))

    def test_overlap_helper_same_day(self):
        from app.storage import _periods_overlap
        d = date(2026, 3, 15)
        assert _periods_overlap(d, d, d, d)

    def test_overlap_helper_partial(self):
        from app.storage import _periods_overlap
        assert _periods_overlap(date(2026,1,1), date(2026,1,10),
                                date(2026,1,8), date(2026,1,20))

    def test_overlap_helper_contained(self):
        from app.storage import _periods_overlap
        assert _periods_overlap(date(2026,1,1), date(2026,1,31),
                                date(2026,1,10), date(2026,1,20))

    def test_no_overlap_before(self):
        from app.storage import _periods_overlap
        assert not _periods_overlap(date(2026,1,1), date(2026,1,5),
                                    date(2026,2,1), date(2026,2,28))

    # ── DB-backed overlap detection (6C-1, 6C-3) ─────────────────────────────

    def test_get_overlapping_returns_conflict(self):
        import app.storage as storage
        emp = self._emp()
        self._period(emp.id, date(2026,3,1), date(2026,3,10))

        # New period [Mar 8–15] overlaps the existing [Mar 1–10]
        conflicts = storage.get_overlapping_wfh_periods(
            emp.id, date(2026,3,8), date(2026,3,15)
        )
        assert len(conflicts) == 1

    def test_get_overlapping_no_conflict(self):
        import app.storage as storage
        emp = self._emp()
        self._period(emp.id, date(2026,3,1), date(2026,3,5))

        conflicts = storage.get_overlapping_wfh_periods(
            emp.id, date(2026,3,6), date(2026,3,10)
        )
        assert len(conflicts) == 0

    def test_exclude_id_skips_own_period_on_update(self):
        import app.storage as storage
        emp = self._emp()
        existing = self._period(emp.id, date(2026,4,1), date(2026,4,10))

        # Editing the same period to the same date range should NOT conflict
        conflicts = storage.get_overlapping_wfh_periods(
            emp.id, date(2026,4,1), date(2026,4,10), exclude_id=existing.id
        )
        assert len(conflicts) == 0

    def test_different_employee_no_conflict(self):
        import app.storage as storage
        emp1 = self._emp()
        emp2 = self._emp()
        self._period(emp1.id, date(2026,5,1), date(2026,5,15))

        # emp2 overlapping dates should NOT conflict with emp1's period
        conflicts = storage.get_overlapping_wfh_periods(
            emp2.id, date(2026,5,1), date(2026,5,15)
        )
        assert len(conflicts) == 0

    def test_create_then_delete(self):
        import app.storage as storage
        emp = self._emp()
        p = self._period(emp.id, date(2026,6,1), date(2026,6,5))

        deleted = storage.delete_wfh_period(p.id)
        assert deleted is True
        assert storage.get_wfh_period_by_id(p.id) is None

    def test_delete_nonexistent_returns_false(self):
        import app.storage as storage
        assert storage.delete_wfh_period("no-such-id") is False


# ══════════════════════════════════════════════════════════════════════════════
# F-1 — SSE token generation & expiry
# ══════════════════════════════════════════════════════════════════════════════

class TestSSEToken:
    """
    Pure unit tests — no HTTP, no database required.
    The conftest DB fixture still runs (autouse) but is unused here.
    """

    def _dummy_user(self):
        from app.models import User, UserRole
        return User(
            id="u-sse-test",
            name="SSE Tester",
            email="ssetest@test.com",
            password_hash="x",
            role=UserRole.ADMIN,
            is_active=True,
        )

    # ── creation ─────────────────────────────────────────────────────────────

    def test_create_sse_token_returns_token_and_expires(self):
        from app.auth import create_sse_token
        result = create_sse_token(self._dummy_user())

        assert "token"      in result
        assert "expires_in" in result
        assert result["expires_in"] == 60
        assert len(result["token"]) > 50   # looks like a JWT

    def test_tokens_are_unique_per_call(self):
        from app.auth import create_sse_token
        u = self._dummy_user()
        t1 = create_sse_token(u)["token"]
        t2 = create_sse_token(u)["token"]
        assert t1 != t2

    def test_token_type_claim_is_sse(self):
        from app.auth import create_sse_token, verify_token
        token = create_sse_token(self._dummy_user())["token"]
        payload = verify_token(token)
        assert payload is not None
        assert payload["type"] == "sse"
        assert payload["sub"]  == "ssetest@test.com"

    # ── single-use (consume + replay) ────────────────────────────────────────

    def test_validate_first_use_returns_user(self):
        from app.auth import create_sse_token, validate_and_consume_sse_token
        import app.storage as storage

        # Ensure the user exists in the in-memory DB
        storage.create_user(self._dummy_user())

        token = create_sse_token(self._dummy_user())["token"]
        user  = validate_and_consume_sse_token(token)
        assert user is not None
        assert user.email == "ssetest@test.com"

    def test_validate_replay_returns_none(self):
        from app.auth import create_sse_token, validate_and_consume_sse_token
        import app.storage as storage

        storage.create_user(self._dummy_user())
        token = create_sse_token(self._dummy_user())["token"]

        first  = validate_and_consume_sse_token(token)
        second = validate_and_consume_sse_token(token)  # replay

        assert first  is not None
        assert second is None

    def test_validate_expired_token_returns_none(self):
        """Simulate an expired token by back-dating the exp claim in the store."""
        from app.auth import (
            create_sse_token, validate_and_consume_sse_token,
            verify_token, _sse_store, _sse_lock,
        )
        import app.storage as storage

        storage.create_user(self._dummy_user())
        token   = create_sse_token(self._dummy_user())["token"]
        payload = verify_token(token)
        jti     = payload["jti"]

        # Backdate the expiry in the store so it looks expired
        with _sse_lock:
            _sse_store[jti]["expires_at"] = datetime.utcnow() - timedelta(seconds=1)

        result = validate_and_consume_sse_token(token)
        assert result is None

    def test_validate_garbage_token_returns_none(self):
        from app.auth import validate_and_consume_sse_token
        assert validate_and_consume_sse_token("not.a.valid.jwt") is None

    def test_validate_regular_access_token_rejected(self):
        """A normal access JWT (no type='sse') must be rejected."""
        from app.auth import create_access_token, validate_and_consume_sse_token

        token  = create_access_token({"sub": "ssetest@test.com"})
        result = validate_and_consume_sse_token(token)
        assert result is None
