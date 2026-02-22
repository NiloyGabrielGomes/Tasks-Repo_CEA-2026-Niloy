from fastapi import APIRouter, HTTPException, Query, Depends, status
from datetime import date
from app.models import User, UserRole
from app.auth import require_role
from app import auth as auth_service
from app import storage
from app.schemas import TeamParticipationResponse, TeamMemberParticipation

router = APIRouter(prefix="/api/teams", tags=["Teams"])


# ===========================
# List All Team Names
# ===========================

@router.get("")
async def get_teams(
    current_user: User = Depends(auth_service.get_current_user),
):
    """Return a sorted list of all unique team names."""
    teams = storage.get_all_teams()
    return {"teams": teams}


# ===========================
# My Team's Participation
# ===========================

@router.get("/me", response_model=TeamParticipationResponse)
async def get_my_team_participation(
    target_date: date = Query(None, description="Date in YYYY-MM-DD (defaults to today)"),
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN])),
):
    """
    Get participation grid for the current user's team.
    Team Leads see their own team; Admins see their own team by default.
    """
    if not current_user.team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not assigned to any team",
        )

    day = target_date or date.today()
    members_data = storage.get_team_participation(current_user.team, day)

    members = [TeamMemberParticipation(**m) for m in members_data]

    return TeamParticipationResponse(
        team=current_user.team,
        date=day.isoformat(),
        members=members,
        total_members=len(members),
    )


# ===========================
# All Teams' Participation (Admin)
# ===========================

@router.get("/all")
async def get_all_teams_participation(
    target_date: date = Query(None, description="Date in YYYY-MM-DD (defaults to today)"),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """
    Get participation grids for every team. Admin only.
    Returns a list of TeamParticipationResponse objects.
    """
    day = target_date or date.today()
    teams = storage.get_all_teams()

    results = []
    for team_name in teams:
        members_data = storage.get_team_participation(team_name, day)
        members = [TeamMemberParticipation(**m) for m in members_data]
        results.append(
            TeamParticipationResponse(
                team=team_name,
                date=day.isoformat(),
                members=members,
                total_members=len(members),
            )
        )

    return {"teams": [r.model_dump() for r in results]}


# ===========================
# Specific Team Participation (Admin)
# ===========================

@router.get("/{team_name}", response_model=TeamParticipationResponse)
async def get_team_participation(
    team_name: str,
    target_date: date = Query(None, description="Date in YYYY-MM-DD (defaults to today)"),
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN])),
):

    if current_user.role == UserRole.TEAM_LEAD and current_user.team != team_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own team's participation",
        )

    day = target_date or date.today()

    all_teams = storage.get_all_teams()
    if team_name not in all_teams:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team '{team_name}' not found",
        )

    members_data = storage.get_team_participation(team_name, day)
    members = [TeamMemberParticipation(**m) for m in members_data]

    return TeamParticipationResponse(
        team=team_name,
        date=day.isoformat(),
        members=members,
        total_members=len(members),
    )
