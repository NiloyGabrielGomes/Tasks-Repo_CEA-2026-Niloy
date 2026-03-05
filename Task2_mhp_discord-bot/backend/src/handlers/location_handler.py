# Handles /work-location slash command and location button interactions
import logging
from datetime import date
from typing import Any, Dict

from src.handlers.auth import AuthenticatedUser
from src.models import WorkLocationType
from src.services.location_service import location_service, LOCATION_DISPLAY
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

# Custom ID prefix for work-location buttons
LOCATION_SET_PREFIX = "location_set"


def _get_command_options(interaction: Dict[str, Any]) -> dict[str, Any]:
    data = interaction.get("data", {})
    options = data.get("options", [])
    return {opt["name"]: opt["value"] for opt in options}


# ── Embed builder ────────────────────────────────────────────────────────────

def _build_location_status_embed(
    discord_id: str, target_date: date, confirmation: str | None = None
) -> Dict[str, Any]:
    record = location_service.get_user_location_for_date(discord_id, target_date)
    current = location_service.get_current_location(record)
    display = location_service.get_location_display_info(current)

    status_line = f"{display['emoji']} **{display['label']}**"

    description_parts = [
        f"📅 **{format_date_display(target_date)}**",
        "",
        f"Current location: {status_line}",
    ]

    if confirmation:
        description_parts.insert(2, confirmation)
        description_parts.insert(3, "")

    description_parts.append("")
    description_parts.append("Click a button below to change your work location.")

    embed = {
        "title": "📍 Work Location",
        "description": "\n".join(description_parts),
        "color": 0x57F287 if current == WorkLocationType.OFFICE else 0xFEE75C,
        "footer": {
            "text": "Default: Office • WFH days count toward monthly cap"
        },
    }

    return embed

