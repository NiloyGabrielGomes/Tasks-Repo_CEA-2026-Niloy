import logging
from datetime import date
from typing import Any, Dict

from src.adapters.base import UIRenderer
from src.adapters.normalized import NormalizedInteraction
from src.models import MealType, WorkLocationType, UserRole
from src.services.override_service import override_service
from src.services.meal_service import MEAL_DISPLAY, DEFAULT_MEAL_TYPES
from src.services.location_service import LOCATION_DISPLAY
from src.services.team_helpers import extract_team_from_roles
from src.storage.dynamodb import storage as db
from src.utils import parse_date_option, validate_date_for_update

logger = logging.getLogger(__name__)

# Custom ID prefixes for override buttons
OVERRIDE_MEAL_PREFIX = "override_meal"
OVERRIDE_LOC_PREFIX = "override_loc"


def handle_override_update(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    try:
        options = interaction.options
        target_user_id = options.get("employee")
        date_str = options.get("date")

        if not target_user_id:
            return renderer.render_error("Please select an employee to override.")

        target_user = None
        if "@" in target_user_id:
            # Email address — resolve via identity mapping
            target_user = db.get_user_by_identity("google_chat", target_user_id)
            if target_user:
                target_user_id = target_user.user_id
        elif target_user_id.startswith("users/"):
            # Google Chat user ID from @mention — resolve via identity mapping
            target_user = db.get_user_by_identity("google_chat", target_user_id)
            if target_user:
                target_user_id = target_user.user_id
        else:
            # Direct user ID (e.g. Discord snowflake)
            target_user = db.get_user(target_user_id)

        if not target_user:
            return renderer.render_error("Employee not found. Please check the email or user ID and try again.")

        try:
            target_date = parse_date_option(date_str)
        except ValueError as e:
            return renderer.render_error(str(e))

        is_valid, error_msg = validate_date_for_update(target_date)
        if not is_valid:
            return renderer.render_error(error_msg)

        # Resolve target team — prefer Discord resolved member, fall back to DB user
        target_team = None
        resolved_member = options.get("_resolved_member_employee")
        if resolved_member:
            target_roles = resolved_member.get("roles", [])
            target_team = extract_team_from_roles(target_roles)
        elif target_user and target_user.team:
            target_team = target_user.team

        allowed, scope_err = override_service.check_team_scope(
            actor_role=interaction.user.role,
            actor_team=interaction.user.team,
            target_team=target_team,
        )
        if not allowed:
            return renderer.render_error(scope_err.lstrip("❌ "))

        current_state = override_service.get_target_current_state(target_user_id, target_date)
        resolved_user = options.get("_resolved_user_employee", {})
        target_username = (
            resolved_user.get("username")
            or options.get("_mention_display_name")
            or (target_user.name if target_user else target_user_id)
        )

        # Google Chat: apply override directly if meal or location param is given
        if interaction.platform == "google_chat":
            meal_param = options.get("meal")
            location_param = options.get("location")

            if meal_param:
                try:
                    meal_type = MealType(meal_param.lower())
                except ValueError:
                    return renderer.render_error(
                        f"Unknown meal type: **{meal_param}**. Use {', '.join(f'`{m.value}`' for m in DEFAULT_MEAL_TYPES)}."
                    )
                current_is_in = current_state["meals"].get(meal_type, True)
                new_is_participating = not current_is_in

                success, result = override_service.override_meal(
                    target_user_id=target_user_id,
                    target_date=target_date,
                    meal_type=meal_type,
                    is_participating=new_is_participating,
                    actor_id=interaction.user.user_id,
                    target_team=target_team,
                )
                if not success:
                    return renderer.render_error(result)

                current_state = override_service.get_target_current_state(target_user_id, target_date)
                display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
                status_text = "✅ Opted In" if new_is_participating else "❌ Opted Out"
                confirmation = (
                    f"✅ Updated {display['emoji']} {display['label']} → {status_text} "
                    f"for {target_username}"
                )
                return renderer.render_override_status(
                    target_user_id, target_username, interaction.user.user_id,
                    target_date, current_state, confirmation=confirmation,
                    target_team=target_team,
                )

            if location_param:
                try:
                    location = WorkLocationType(location_param.lower())
                except ValueError:
                    return renderer.render_error(
                        f"Unknown location: **{location_param}**. Use `office` or `wfh`."
                    )
                success, result = override_service.override_location(
                    target_user_id=target_user_id,
                    target_date=target_date,
                    location=location,
                    actor_id=interaction.user.user_id,
                    target_team=target_team,
                )
                if not success:
                    return renderer.render_error(result)

                current_state = override_service.get_target_current_state(target_user_id, target_date)
                loc_display = LOCATION_DISPLAY.get(location, {"label": location.value, "emoji": "📍"})
                confirmation = (
                    f"✅ Updated {loc_display['emoji']} Work Location → "
                    f"**{loc_display['label']}** for {target_username}"
                )
                return renderer.render_override_status(
                    target_user_id, target_username, interaction.user.user_id,
                    target_date, current_state, confirmation=confirmation,
                    target_team=target_team,
                )

        return renderer.render_override_status(
            target_user_id, target_username, interaction.user.user_id, target_date, current_state,
            target_team=target_team,
        )

    except Exception as e:
        logger.exception("Error handling override-update: %s", e)
        return renderer.render_error("An error occurred while processing the override. Please try again.")


def handle_override_meal(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    try:
        action_id = interaction.action_id or ""

        parts = action_id.split(":")
        if len(parts) != 7 or parts[0] != OVERRIDE_MEAL_PREFIX:
            return renderer.render_error("Invalid button interaction.")

        _, actor_id, target_user_id, date_str, meal_type_str, state_str, target_team_str = parts

        # Security: only the original actor can click
        if interaction.user.user_id != actor_id:
            return renderer.render_error("Only the user who initiated the override can use these buttons.")

        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            return renderer.render_error("Invalid date format in button.")

        try:
            meal_type = MealType(meal_type_str)
        except ValueError:
            return renderer.render_error(f"Unknown meal type: {meal_type_str}")

        is_participating = state_str == "in"
        target_team = target_team_str or None

        # Re-validate team scope on every button click to prevent cross-team bypass
        allowed, scope_err = override_service.check_team_scope(
            actor_role=interaction.user.role,
            actor_team=interaction.user.team,
            target_team=target_team,
        )
        if not allowed:
            return renderer.render_error(scope_err.lstrip("❌ "))

        success, result = override_service.override_meal(
            target_user_id=target_user_id,
            target_date=target_date,
            meal_type=meal_type,
            is_participating=is_participating,
            actor_id=interaction.user.user_id,
            target_team=target_team,
        )

        if not success:
            return renderer.render_error(result)

        current_state = override_service.get_target_current_state(target_user_id, target_date)
        display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
        status_text = "✅ Opted In" if is_participating else "❌ Opted Out"
        confirmation = (
            f"✅ Updated **{display['emoji']} {display['label']}** → {status_text} "
            f"for <@{target_user_id}>"
        )

        status = renderer.render_override_status(
            target_user_id, target_user_id, actor_id, target_date, current_state, confirmation,
            target_team=target_team,
        )
        return renderer.render_update(status)

    except Exception as e:
        logger.exception("Error handling override meal: %s", e)
        return renderer.render_error("An error occurred while processing the meal override. Please try again.")


def handle_override_location(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    try:
        action_id = interaction.action_id or ""

        parts = action_id.split(":")
        if len(parts) != 6 or parts[0] != OVERRIDE_LOC_PREFIX:
            return renderer.render_error("Invalid button interaction.")

        _, actor_id, target_user_id, date_str, loc_str, target_team_str = parts

        if interaction.user.user_id != actor_id:
            return renderer.render_error("Only the user who initiated the override can use these buttons.")

        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            return renderer.render_error("Invalid date format in button.")

        try:
            location = WorkLocationType(loc_str)
        except ValueError:
            return renderer.render_error(f"Unknown location type: {loc_str}")

        target_team = target_team_str or None

        # Re-validate team scope on every button click to prevent cross-team bypass
        allowed, scope_err = override_service.check_team_scope(
            actor_role=interaction.user.role,
            actor_team=interaction.user.team,
            target_team=target_team,
        )
        if not allowed:
            return renderer.render_error(scope_err.lstrip("❌ "))

        success, result = override_service.override_location(
            target_user_id=target_user_id,
            target_date=target_date,
            location=location,
            actor_id=interaction.user.user_id,
            target_team=target_team,
        )

        if not success:
            return renderer.render_error(result)

        current_state = override_service.get_target_current_state(target_user_id, target_date)
        loc_display = LOCATION_DISPLAY.get(location, {"label": location.value, "emoji": "📍"})
        confirmation = (
            f"✅ Updated **{loc_display['emoji']} Work Location** → "
            f"**{loc_display['label']}** for <@{target_user_id}>"
        )

        status = renderer.render_override_status(
            target_user_id, target_user_id, actor_id, target_date, current_state, confirmation,
            target_team=target_team,
        )
        return renderer.render_update(status)

    except Exception as e:
        logger.exception("Error handling override location: %s", e)
        return renderer.render_error("An error occurred while processing the location override. Please try again.")


# ── Feature Lambda entry point ────────────────────────────────────────────────

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    from src.adapters.discord.renderer import DiscordRenderer
    from src.adapters.discord.ingress_adapter import _parse_command_options
    from src.handlers.auth import AuthenticatedUser

    renderer = DiscordRenderer()

    try:
        user_dict = event["user"]
        user = AuthenticatedUser(
            user_id=user_dict["user_id"],
            username=user_dict["username"],
            display_name=user_dict.get("display_name"),
            role=UserRole(user_dict["role"]),
            team=user_dict.get("team"),
            space_id=user_dict.get("space_id", ""),
            platform_roles=user_dict.get("platform_roles", []),
            platform=user_dict.get("platform", "discord"),
        )

        raw_interaction = event.get("interaction", {})
        dispatch_type = event["dispatch_type"]

        if dispatch_type == "command":
            options = event.get("options") or _parse_command_options(raw_interaction.get("data", {}))
            action_id = None
        else:
            options = {}
            action_id = event.get("action_id") or raw_interaction.get("data", {}).get("custom_id")

        normalized = NormalizedInteraction(
            platform=user_dict.get("platform", "discord"),
            interaction_type=dispatch_type,
            command_name=event.get("command_name"),
            action_id=action_id,
            options=options,
            raw_body=raw_interaction,
            user=user,
        )
    except KeyError as e:
        logger.error("Malformed dispatch event, missing key: %s", e)
        return renderer.render_error(f"Internal error: missing required field {e}")

    if dispatch_type == "command":
        return handle_override_update(normalized, renderer)
    else:
        custom_id = action_id or ""
        if custom_id.startswith(OVERRIDE_MEAL_PREFIX):
            return handle_override_meal(normalized, renderer)
        if custom_id.startswith(OVERRIDE_LOC_PREFIX):
            return handle_override_location(normalized, renderer)
        return renderer.render_error("Unknown override component.")
