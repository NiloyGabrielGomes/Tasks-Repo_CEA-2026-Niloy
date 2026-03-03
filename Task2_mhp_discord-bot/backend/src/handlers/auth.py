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


