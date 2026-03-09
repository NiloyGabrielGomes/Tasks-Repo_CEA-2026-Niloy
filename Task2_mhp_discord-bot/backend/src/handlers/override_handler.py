import logging
from datetime import date
from typing import Any, Dict

from src.handlers.auth import AuthenticatedUser
from src.models import MealType, WorkLocationType, UserRole
from src.services.override_service import override_service
from src.services.meal_service import MEAL_DISPLAY, DEFAULT_MEAL_TYPES
from src.services.location_service import LOCATION_DISPLAY
from src.services.discord_helpers import extract_team_from_roles
from src.utils import parse_date_option, format_date_display, validate_date_for_update

logger = logging.getLogger(__name__)

# Discord response types
RESPONSE_CHANNEL_MESSAGE = 4
RESPONSE_UPDATE_MESSAGE = 7

# Discord component types
ACTION_ROW = 1
BUTTON = 2

# Discord button styles
BUTTON_PRIMARY = 1    # Blurple
BUTTON_SECONDARY = 2  # Grey
BUTTON_SUCCESS = 3    # Green
BUTTON_DANGER = 4     # Red

# Custom ID prefixes for override buttons
OVERRIDE_MEAL_PREFIX = "override_meal"
OVERRIDE_LOC_PREFIX = "override_loc"

# Embed color
OVERRIDE_EMBED_COLOR = 0xED4245  # Red — distinct from self-service


def _get_command_options(interaction: Dict[str, Any]) -> dict[str, Any]:
    data = interaction.get("data", {})
    options = data.get("options", [])
    result: dict[str, Any] = {}
    for opt in options:
        if opt.get("type") == 6:  # USER type
            result[opt["name"]] = opt["value"]
            # Also capture resolved user data if available
            resolved = data.get("resolved", {})
            members = resolved.get("members", {})
            users = resolved.get("users", {})
            if opt["value"] in users:
                result[f"_resolved_user_{opt['name']}"] = users[opt["value"]]
            if opt["value"] in members:
                result[f"_resolved_member_{opt['name']}"] = members[opt["value"]]
        else:
            result[opt["name"]] = opt["value"]
    return result