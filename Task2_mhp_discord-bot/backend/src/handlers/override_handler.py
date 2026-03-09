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

# ── Embed builder ────────────────────────────────────────────────────────────

def _build_override_embed(
    target_user_id: str,
    target_username: str,
    target_date: date,
    current_state: dict,
    confirmation: str | None = None,
) -> Dict[str, Any]:
    # Meal fields
    fields = []
    for meal_type in DEFAULT_MEAL_TYPES:
        display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
        is_in = current_state["meals"].get(meal_type, True)
        status_emoji = "✅" if is_in else "❌"
        status_text = "Opted In" if is_in else "Opted Out"
        fields.append({
            "name": f"{display['emoji']} {display['label']}",
            "value": f"{status_emoji} {status_text}",
            "inline": True,
        })

    # Location field
    loc = current_state["location"]
    loc_display = LOCATION_DISPLAY.get(loc, {"label": loc.value, "emoji": "📍"})
    fields.append({
        "name": f"{loc_display['emoji']} Work Location",
        "value": f"**{loc_display['label']}**",
        "inline": True,
    })

    description_parts = [
        f"👤 **Employee:** <@{target_user_id}>"
        f" ({target_username})",
        f"📅 **Date:** {format_date_display(target_date)}",
    ]

    if confirmation:
        description_parts.append("")
        description_parts.append(confirmation)

    description_parts.append("")
    description_parts.append("Use the buttons below to update this employee's records.")

    embed = {
        "title": "🔧 Override Update",
        "description": "\n".join(description_parts),
        "fields": fields,
        "color": OVERRIDE_EMBED_COLOR,
        "footer": {
            "text": "Overrides are recorded for audit purposes"
        },
    }

    return embed

# ── Button builder ───────────────────────────────────────────────────────────

def _build_override_buttons(
    actor_id: str,
    target_user_id: str,
    target_date: date,
    current_state: dict,
) -> list[Dict[str, Any]]:
    # Meal buttons (row 1)
    meal_buttons: list[Dict[str, Any]] = []
    for meal_type in DEFAULT_MEAL_TYPES:
        display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
        is_in = current_state["meals"].get(meal_type, True)

        # Button will toggle to the opposite state
        new_state = "out" if is_in else "in"
        custom_id = (
            f"{OVERRIDE_MEAL_PREFIX}:{actor_id}:{target_user_id}"
            f":{target_date.isoformat()}:{meal_type.value}:{new_state}"
        )

        if is_in:
            style = BUTTON_SUCCESS
            label = f"{display['emoji']} {display['label']} ✅"
        else:
            style = BUTTON_DANGER
            label = f"{display['emoji']} {display['label']} ❌"

        meal_buttons.append({
            "type": BUTTON,
            "style": style,
            "label": label,
            "custom_id": custom_id,
        })

    # Location buttons (row 2)
    loc_buttons: list[Dict[str, Any]] = []
    current_loc = current_state["location"]
    for loc_type in (WorkLocationType.OFFICE, WorkLocationType.WFH):
        loc_display = LOCATION_DISPLAY.get(loc_type, {"label": loc_type.value, "emoji": "📍"})
        is_active = loc_type == current_loc
        custom_id = (
            f"{OVERRIDE_LOC_PREFIX}:{actor_id}:{target_user_id}"
            f":{target_date.isoformat()}:{loc_type.value}"
        )

        if is_active:
            style = BUTTON_SUCCESS
            label = f"{loc_display['emoji']} {loc_display['label']} ✅"
        else:
            style = BUTTON_SECONDARY
            label = f"{loc_display['emoji']} {loc_display['label']}"

        loc_buttons.append({
            "type": BUTTON,
            "style": style,
            "label": label,
            "custom_id": custom_id,
            "disabled": is_active,
        })

    rows = [
        {"type": ACTION_ROW, "components": meal_buttons},
        {"type": ACTION_ROW, "components": loc_buttons},
    ]
    return rows

# ── Command handler ──────────────────────────────────────────────────────────

def handle_override_update(
    interaction: Dict[str, Any], user: AuthenticatedUser
) -> Dict[str, Any]:
    try:
        options = _get_command_options(interaction)
        target_user_id = options.get("employee")
        date_str = options.get("date")

        if not target_user_id:
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {
                    "content": "❌ Please select an employee to override.",
                    "flags": 64,
                },
            }

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

        target_team = None
        resolved_member = options.get(f"_resolved_member_employee")
        if resolved_member:
            target_roles = resolved_member.get("roles", [])
            target_team = extract_team_from_roles(target_roles)

        # Team scope check
        allowed, scope_err = override_service.check_team_scope(
            actor_role=user.role,
            actor_team=user.team,
            target_team=target_team,
        )
        if not allowed:
            return {
                "type": RESPONSE_CHANNEL_MESSAGE,
                "data": {"content": scope_err, "flags": 64},
            }

        current_state = override_service.get_target_current_state(
            target_user_id, target_date
        )

        resolved_user = options.get(f"_resolved_user_employee", {})
        target_username = resolved_user.get("username", target_user_id)

        embed = _build_override_embed(
            target_user_id, target_username, target_date, current_state
        )
        components = _build_override_buttons(
            user.discord_id, target_user_id, target_date, current_state
        )

        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {
                "embeds": [embed],
                "components": components,
                "flags": 64,
            },
        }

    except Exception as e:
        logger.exception("Error handling override-update: %s", e)
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {
                "content": "❌ An error occurred while processing the override. Please try again.",
                "flags": 64,
            },
        }

