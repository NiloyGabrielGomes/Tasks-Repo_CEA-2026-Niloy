# Handles /meal-update slash command and meal toggle button interactions
import logging
from datetime import date
from typing import Any, Dict

from src.handlers.auth import AuthenticatedUser
from src.models import MealType, UserRole
from src.services.meal_service import meal_service, MEAL_DISPLAY
from src.utils import parse_date_option, format_date_display, validate_date_for_update

logger = logging.getLogger(__name__)

# Discord response types
RESPONSE_CHANNEL_MESSAGE = 4
RESPONSE_UPDATE_MESSAGE = 7

# Discord component types
ACTION_ROW = 1
BUTTON = 2

# Discord button styles
BUTTON_PRIMARY = 1    # Blurple (opted in)
BUTTON_SECONDARY = 2  # Grey
BUTTON_SUCCESS = 3    # Green (opted in)
BUTTON_DANGER = 4     # Red (opted out)

# Custom ID prefix for meal toggle buttons
MEAL_TOGGLE_PREFIX = "meal_toggle"

def _get_command_options(interaction: Dict[str, Any]) -> dict[str, Any]:
    data = interaction.get("data", {})
    options = data.get("options", [])
    return {opt["name"]: opt["value"] for opt in options}


def _build_meal_status_embed(
    discord_id: str, target_date: date
) -> Dict[str, Any]:
    meals = meal_service.get_user_meals_for_date(discord_id, target_date)

    fields = []
    for meal_type, record in meals.items():
        display = meal_service.get_meal_display_info(meal_type)
        is_participating = meal_service.get_participation_status(record)

        status_emoji = "✅" if is_participating else "❌"
        status_text = "Opted In" if is_participating else "Opted Out"

        fields.append({
            "name": f"{display['emoji']} {display['label']}",
            "value": f"{status_emoji} {status_text}",
            "inline": True,
        })

    embed = {
        "title": "🍽️ Meal Participation",
        "description": f"📅 **{format_date_display(target_date)}**\n\nClick a button below to toggle your participation for each meal.",
        "fields": fields,
        "color": 0x5865F2,  # Discord blurple
        "footer": {
            "text": "Default: Opted In for all meals • Toggle to change"
        },
    }

    return embed


def _build_meal_toggle_buttons(
    discord_id: str, target_date: date
) -> list[Dict[str, Any]]:
    meals = meal_service.get_user_meals_for_date(discord_id, target_date)

    buttons = []
    for meal_type, record in meals.items():
        display = meal_service.get_meal_display_info(meal_type)
        is_participating = meal_service.get_participation_status(record)

        # custom_id format: meal_toggle:<discord_id>:<date>:<meal_type>
        custom_id = f"{MEAL_TOGGLE_PREFIX}:{discord_id}:{target_date.isoformat()}:{meal_type.value}"

        if is_participating:
            style = BUTTON_SUCCESS
            label = f"{display['emoji']} {display['label']} ✅"
        else:
            style = BUTTON_DANGER
            label = f"{display['emoji']} {display['label']} ❌"

        buttons.append({
            "type": BUTTON,
            "style": style,
            "label": label,
            "custom_id": custom_id,
        })

    # Discord allows max 5 buttons per action row
    rows = []
    for i in range(0, len(buttons), 5):
        rows.append({
            "type": ACTION_ROW,
            "components": buttons[i:i + 5],
        })

    return rows


def handle_meal_update(
    interaction: Dict[str, Any], user: AuthenticatedUser
) -> Dict[str, Any]:
    try:
        options = _get_command_options(interaction)
        date_str = options.get("date")

        try:
            target_date = parse_date_option(date_str)
        except ValueError as e:
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {
                    "content": f"❌ {str(e)}",
                    "flags": 64,
                },
            }

        is_valid, error_msg = validate_date_for_update(target_date)
        if not is_valid:
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {
                    "content": f"❌ {error_msg}",
                    "flags": 64,
                },
            }

        embed = _build_meal_status_embed(user.discord_id, target_date)
        components = _build_meal_toggle_buttons(user.discord_id, target_date)

        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {
                "embeds": [embed],
                "components": components,
                "flags": 64,  # Ephemeral
            },
        }

    except Exception as e:
        logger.exception(f"Error handling meal-update: {e}")
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {
                "content": "❌ An error occurred while fetching your meal status. Please try again.",
                "flags": 64,
            },
        }


def handle_meal_toggle(
    interaction: Dict[str, Any], user: AuthenticatedUser
) -> Dict[str, Any]:
    try:
        data = interaction.get("data", {})
        custom_id = data.get("custom_id", "")

        # Parse custom_id: meal_toggle:<discord_id>:<date>:<meal_type>
        parts = custom_id.split(":")
        if len(parts) != 4 or parts[0] != MEAL_TOGGLE_PREFIX:
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {
                    "content": "❌ Invalid button interaction.",
                    "flags": 64,
                },
            }

        _, target_user_id, date_str, meal_type_str = parts

        # Security: ensure the clicking user matches the button target
        if user.discord_id != target_user_id:
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {
                    "content": "❌ You can only update your own meal participation.",
                    "flags": 64,
                },
            }

        target_date = date.fromisoformat(date_str)
        meal_type = MealType(meal_type_str)

        # Toggle
        success, result = meal_service.toggle_meal_participation(
            discord_id=user.discord_id,
            target_date=target_date,
            meal_type=meal_type,
            updated_by=user.discord_id,
            team=user.team,
        )

        if not success:
            # result is an error message string
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {
                    "content": f"❌ {result}",
                    "flags": 64,
                },
            }

        # Build updated embed + buttons showing new state
        embed = _build_meal_status_embed(user.discord_id, target_date)
        components = _build_meal_toggle_buttons(user.discord_id, target_date)

        # Add confirmation text to embed description
        display = meal_service.get_meal_display_info(meal_type)
        status_text = "✅ Opted In" if result.is_participating else "❌ Opted Out"
        embed["description"] = (
            f"📅 **{format_date_display(target_date)}**\n\n"
            f"Updated **{display['emoji']} {display['label']}** → {status_text}\n\n"
            f"Click a button below to toggle your participation for each meal."
        )

        # Use UPDATE_MESSAGE to edit the original response in place
        return {
            "type": RESPONSE_UPDATE_MESSAGE,
            "data": {
                "embeds": [embed],
                "components": components,
            },
        }

    except Exception as e:
        logger.exception(f"Error handling meal toggle: {e}")
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {
                "content": "❌ An error occurred while updating your meal status. Please try again.",
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
        return handle_meal_update(interaction, user)
    else:
        return handle_meal_toggle(interaction, user)
