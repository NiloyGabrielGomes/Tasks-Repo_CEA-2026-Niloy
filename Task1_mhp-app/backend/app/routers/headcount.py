from fastapi import APIRouter, Query, Depends
from datetime import date
from typing import Optional

from app.models import User, UserRole
from app.auth import require_role
from app import auth as auth_service
from app import storage
from app import utils
from app.schemas import (
    HeadcountByTeamResponse,
    HeadcountByLocationResponse,
    HeadcountTeamEntry,
    HeadcountMemberEntry,
    HeadcountLocationEntry,
)

router = APIRouter(prefix="/api/headcount", tags=["Headcount"])


# ── helpers ────────────────────────────────────────────────────────────────

def _build_team_response(target_date: date, team_filter: Optional[str]) -> HeadcountByTeamResponse:
    breakdowns = storage.get_headcount_by_team_breakdown(target_date, team_filter=team_filter)
    total = sum(t["total_members"] for t in breakdowns)

    teams = [
        HeadcountTeamEntry(
            team=t["team"],
            total_members=t["total_members"],
            office_count=t["office_count"],
            wfh_count=t["wfh_count"],
            members=[HeadcountMemberEntry(**m) for m in t["members"]],
        )
        for t in breakdowns
    ]
    return HeadcountByTeamResponse(date=target_date, total_employees=total, teams=teams)


def _build_location_response(target_date: date, team_filter: Optional[str]) -> HeadcountByLocationResponse:
    data = storage.get_headcount_by_location_breakdown(target_date, team_filter=team_filter)

    locations = [
        HeadcountLocationEntry(
            location=loc["location"],
            count=loc["count"],
            employees=[HeadcountMemberEntry(**e) for e in loc["employees"]],
        )
        for loc in data["locations"]
    ]
    return HeadcountByLocationResponse(
        date=target_date,
        total_employees=data["total"],
        office_count=data["office_count"],
        wfh_count=data["wfh_count"],
        locations=locations,
    )


# ── endpoints ──────────────────────────────────────────────────────────────

@router.get("/by-team", response_model=HeadcountByTeamResponse)
async def headcount_by_team(
    target_date: date = Query(None, description="Date in YYYY-MM-DD (defaults to today)"),
    team: Optional[str] = Query(None, description="Filter to a specific team name (Admin only)"),
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN])),
):
    
    day = target_date or utils.get_today()

    if current_user.role == UserRole.TEAM_LEAD:
        applied_filter = current_user.team
    else:
        applied_filter = team  # None → all teams

    return _build_team_response(day, team_filter=applied_filter)


@router.get("/by-location", response_model=HeadcountByLocationResponse)
async def headcount_by_location(
    target_date: date = Query(None, description="Date in YYYY-MM-DD (defaults to today)"),
    team: Optional[str] = Query(None, description="Filter to a specific team name (Admin only)"),
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN])),
):
    
    day = target_date or utils.get_today()

    if current_user.role == UserRole.TEAM_LEAD:
        applied_filter = current_user.team
    else:
        applied_filter = team

    return _build_location_response(day, team_filter=applied_filter)
