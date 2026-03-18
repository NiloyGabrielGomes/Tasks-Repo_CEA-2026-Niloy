# Handles /work-location slash command and location button interactions
import logging
from datetime import date
from typing import Any, Dict

from src.handlers.auth import AuthenticatedUser
from src.models import WorkLocationType, UserRole
from src.config import settings
from src.services.discord_follow_up import post_follow_up
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

# ── Button builder ───────────────────────────────────────────────────────────

def _build_location_buttons(
    discord_id: str, target_date: date
) -> list[Dict[str, Any]]:
    record = location_service.get_user_location_for_date(discord_id, target_date)
    current = location_service.get_current_location(record)

    buttons: list[Dict[str, Any]] = []

    for loc_type in (WorkLocationType.OFFICE, WorkLocationType.WFH):
        display = location_service.get_location_display_info(loc_type)
        custom_id = (
            f"{LOCATION_SET_PREFIX}:{discord_id}:"
            f"{target_date.isoformat()}:{loc_type.value}"
        )

        is_active = loc_type == current
        if is_active:
            style = BUTTON_SUCCESS
            label = f"{display['emoji']} {display['label']} ✅"
        else:
            style = BUTTON_SECONDARY
            label = f"{display['emoji']} {display['label']}"

        buttons.append({
            "type": BUTTON,
            "style": style,
            "label": label,
            "custom_id": custom_id,
            "disabled": is_active,  # can't re-select the current location
        })

    return [{"type": ACTION_ROW, "components": buttons}]

# ── Command handler ──────────────────────────────────────────────────────────

def handle_work_location(
    interaction: Dict[str, Any], user: AuthenticatedUser
) -> Dict[str, Any]:
    try:
        options = _get_command_options(interaction)
        date_str = options.get("date")

        # Parse & validate date
        try:
            target_date = parse_date_option(date_str)
        except ValueError as e:
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {"content": f"❌ {e}", "flags": 64},
            }

        is_valid, error_msg = validate_date_for_update(target_date)
        if not is_valid:
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {"content": f"❌ {error_msg}", "flags": 64},
            }

        embed = _build_location_status_embed(user.discord_id, target_date)
        components = _build_location_buttons(user.discord_id, target_date)

        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {
                "embeds": [embed],
                "components": components,
                "flags": 64,  # Ephemeral
            },
        }

    except Exception as e:
        logger.exception("Error handling work-location: %s", e)
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {
                "content": "❌ An error occurred while fetching your work location. Please try again.",
                "flags": 64,
            },
        }

# ── Button interaction handler ───────────────────────────────────────────────

def handle_location_set(
    interaction: Dict[str, Any], user: AuthenticatedUser
) -> Dict[str, Any]:
    try:
        data = interaction.get("data", {})
        custom_id = data.get("custom_id", "")
        # Parse custom_id: location_set:<discord_id>:<date>:<location>
        parts = custom_id.split(":")
        if len(parts) != 4 or parts[0] != LOCATION_SET_PREFIX:
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {"content": "❌ Invalid button interaction.", "flags": 64},
            }

        _, target_user_id, date_str, location_str = parts

        # Security: only the user themselves can click their own buttons
        if user.discord_id != target_user_id:
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {
                    "content": "❌ You can only update your own work location.",
                    "flags": 64,
                },
            }

        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {"content": "❌ Invalid date format in button.", "flags": 64},
            }
        try:
            location = WorkLocationType(location_str)
        except ValueError:
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {
                    "content": f"❌ Unknown location type: {location_str}",
                    "flags": 64,
                },
            }

        # Persist
        success, result = location_service.set_work_location(
            discord_id=user.discord_id,
            target_date=target_date,
            location=location,
            updated_by=user.discord_id,
            team=user.team,
        )

        if not success:
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {"content": f"❌ {result}", "flags": 64},
            }

        # Build updated embed with confirmation
        display = location_service.get_location_display_info(location)
        confirmation = (
            f"Updated → {display['emoji']} **{display['label']}**"
        )
        embed = _build_location_status_embed(
            user.discord_id, target_date, confirmation=confirmation
        )
        components = _build_location_buttons(user.discord_id, target_date)

        return {
            "type": RESPONSE_UPDATE_MESSAGE,
            "data": {
                "embeds": [embed],
                "components": components,
            },
        }

    except Exception as e:
        logger.exception("Error handling location set: %s", e)
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {
                "content": "❌ An error occurred while updating your work location. Please try again.",
                "flags": 64,
            },
        }


# ── Feature Lambda entry point (Issue #19) ───────────────────────────────────

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    interaction = event["interaction"]
    user_dict = event["user"]
    dispatch_type = event["dispatch_type"]

    user = AuthenticatedUser(
        discord_id=user_dict["discord_id"],
        username=user_dict["username"],
        global_name=user_dict.get("global_name"),
        role=UserRole(user_dict["role"]),
        team=user_dict.get("team"),
        guild_id=user_dict["guild_id"],
        discord_roles=user_dict.get("discord_roles", []),
    )

    if dispatch_type == "command":
        response = handle_work_location(interaction, user)
        post_follow_up(
            settings.DISCORD_APPLICATION_ID,
            interaction["token"],
            response["data"],
        )
        return {"statusCode": 200}
    else:
        return handle_location_set(interaction, user)
