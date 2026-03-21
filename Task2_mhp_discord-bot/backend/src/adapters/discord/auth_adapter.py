"""Discord user resolution — maps Discord role IDs to AuthenticatedUser."""
import logging
from typing import Any, Dict, Optional

from src.adapters.base import UserResolver
from src.config import settings
from src.models import UserRole
from src.services.team_helpers import extract_team_from_roles

logger = logging.getLogger(__name__)


class DiscordUserResolver(UserResolver):

    def resolve(self, raw_body: Dict[str, Any]) -> "AuthenticatedUser":
        from src.handlers.auth import AuthenticatedUser

        member = raw_body.get("member", {})
        user_data = raw_body.get("user", {})

        user_id = member.get("user", {}).get("id") or user_data.get("id", "")
        username = member.get("user", {}).get("username") or user_data.get("username", "")
        display_name = member.get("user", {}).get("global_name") or user_data.get("global_name")
        platform_roles = member.get("roles", [])
        space_id = member.get("guild_id") or raw_body.get("guild_id", "")

        app_role, _ = map_discord_roles_to_app_role(platform_roles)
        team = extract_team_from_roles(platform_roles)

        logger.info(
            f"Discord user resolved: {username} ({user_id}) - Role: {app_role.value}, "
            f"Team: {team}"
        )

        return AuthenticatedUser(
            user_id=user_id,
            username=username,
            display_name=display_name,
            role=app_role,
            team=team,
            space_id=space_id,
            platform_roles=platform_roles,
            platform="discord",
        )


def map_discord_roles_to_app_role(discord_roles: list[str]) -> tuple[UserRole, Optional[str]]:
    if settings.ROLE_ADMIN_ID and settings.ROLE_ADMIN_ID in discord_roles:
        return UserRole.ADMIN, None

    if settings.ROLE_TEAM_LEAD_ID and settings.ROLE_TEAM_LEAD_ID in discord_roles:
        return UserRole.TEAM_LEAD, None

    if discord_roles and not settings.ROLE_ADMIN_ID:
        logger.warning(
            f"Role mapping not configured: ROLE_ADMIN_ID is not set. "
            f"Defaulting to EMPLOYEE."
        )

    return UserRole.EMPLOYEE, None
