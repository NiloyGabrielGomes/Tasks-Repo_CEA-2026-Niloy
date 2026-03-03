import logging
from dataclasses import dataclass
from typing import Optional

from src.config import settings
from src.models import UserRole

logger = logging.getLogger(__name__)


# Role hierarchy (higher index = more permissions)
ROLE_HIERARCHY = {
    UserRole.EMPLOYEE: 0,
    UserRole.TEAM_LEAD: 1,
    UserRole.ADMIN: 2,
}


@dataclass
class AuthenticatedUser:
    discord_id: str
    username: str
    global_name: Optional[str]
    role: UserRole
    team: Optional[str]
    guild_id: str
    discord_roles: list[str]  # Raw Discord role IDs


def get_role_hierarchy_level(role: UserRole) -> int:
    return ROLE_HIERARCHY.get(role, 0)


def map_discord_roles_to_app_role(discord_roles: list[str]) -> tuple[UserRole, Optional[str]]:
    if settings.ROLE_ADMIN_ID and settings.ROLE_ADMIN_ID in discord_roles:
        return UserRole.ADMIN, None
    
    if settings.ROLE_TEAM_LEAD_ID and settings.ROLE_TEAM_LEAD_ID in discord_roles:
        # TODO: Derive team from Discord role name (e.g., "Team-Backend")
        return UserRole.TEAM_LEAD, None
    
    # Log warning if user has roles but no mapping configured
    if discord_roles and not settings.ROLE_ADMIN_ID:
        logger.warning(
            f"Role mapping not configured: ROLE_ADMIN_ID is not set. "
            f"User Discord roles {discord_roles} cannot be mapped to application roles. "
            f"Defaulting to EMPLOYEE. Please configure ROLE_ADMIN_ID and ROLE_TEAM_LEAD_ID."
        )
    
    # Default to Employee
    return UserRole.EMPLOYEE, None


def get_user_from_interaction(interaction: dict) -> AuthenticatedUser:
    member = interaction.get("member", {})
    user = interaction.get("user", {})
    
    discord_id = member.get("user", {}).get("id") or user.get("id", "")
    username = member.get("user", {}).get("username") or user.get("username", "")
    global_name = member.get("user", {}).get("global_name") or user.get("global_name")
    discord_roles = member.get("roles", [])
    guild_id = member.get("guild_id") or interaction.get("guild_id", "")
    
    # Map Discord roles to application role
    app_role, team = map_discord_roles_to_app_role(discord_roles)
    
    logger.info(
        f"Authenticated user: {username} ({discord_id}) - Role: {app_role.value}, "
        f"Discord roles: {discord_roles}"
    )
    
    return AuthenticatedUser(
        discord_id=discord_id,
        username=username,
        global_name=global_name,
        role=app_role,
        team=team,
        guild_id=guild_id,
        discord_roles=discord_roles,
    )


