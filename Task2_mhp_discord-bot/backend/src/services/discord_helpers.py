# Backward-compatibility shim — canonical location is now team_helpers.py
from src.services.team_helpers import (  # noqa: F401
    get_team_role_map,
    invalidate_team_role_cache,
    extract_team_from_roles,
)
