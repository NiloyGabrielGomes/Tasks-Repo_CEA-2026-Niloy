import logging
from dataclasses import dataclass
from typing import Optional

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
    user_id: str                    # platform-agnostic opaque ID
    username: str
    display_name: Optional[str]     # Discord global_name / Google Chat displayName
    role: UserRole
    team: Optional[str]
    space_id: str                   # Discord guild_id / Google Chat space name
    platform_roles: list[str]       # raw platform role IDs
    platform: str = "discord"       # "discord" | "google_chat"


def get_role_hierarchy_level(role: UserRole) -> int:
    return ROLE_HIERARCHY.get(role, 0)


def get_user_from_interaction(interaction: dict) -> AuthenticatedUser:
    
    from src.adapters.discord.auth_adapter import DiscordUserResolver
    return DiscordUserResolver().resolve(interaction)


def authorize_command(
    user: AuthenticatedUser,
    required_role: UserRole
) -> tuple[bool, Optional[str]]:
    user_level = get_role_hierarchy_level(user.role)
    required_level = get_role_hierarchy_level(required_role)

    if user_level < required_level:
        return False, f"❌ You don't have permission to use this command. Required role: {required_role.value}"

    return True, None


# Command role requirements
COMMAND_ROLE_REQUIREMENTS = {
    "meal-update": UserRole.EMPLOYEE,
    "work-location": UserRole.EMPLOYEE,
    "link-identity": UserRole.EMPLOYEE,   
    "team-summary": UserRole.TEAM_LEAD,
    "headcount-summary": UserRole.ADMIN,
    "override-update": UserRole.TEAM_LEAD,
    "generate-summary": UserRole.ADMIN,
}


def check_command_authorization(
    command_name: str,
    user: AuthenticatedUser
) -> tuple[bool, Optional[str]]:
    required_role = COMMAND_ROLE_REQUIREMENTS.get(command_name.lower())

    if required_role is None:
        logger.warning(f"Command '{command_name}' has no role requirement defined")
        return True, None

    return authorize_command(user, required_role)
