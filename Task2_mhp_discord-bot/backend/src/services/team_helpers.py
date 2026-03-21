import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_team_role_map: dict | None = None


def get_team_role_map() -> dict:
    global _team_role_map
    if _team_role_map is None:
        from src.storage.dynamodb import storage
        policy = storage.get_policy("team_role_map")
        if policy:
            try:
                _team_role_map = json.loads(policy.value)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Invalid team_role_map policy value, defaulting to empty")
                _team_role_map = {}
        else:
            logger.info("No team_role_map policy found, defaulting to empty")
            _team_role_map = {}
    return _team_role_map


def invalidate_team_role_cache() -> None:
    global _team_role_map
    _team_role_map = None


def extract_team_from_roles(member_roles: list[str]) -> Optional[str]:
    team_role_map = get_team_role_map()

    for role_id in member_roles:
        if role_id in team_role_map:
            return team_role_map[role_id]
    return None
