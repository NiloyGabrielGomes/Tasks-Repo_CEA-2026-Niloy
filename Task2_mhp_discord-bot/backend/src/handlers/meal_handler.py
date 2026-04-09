# Handles /meal-update slash command and meal toggle button interactions
import logging
from datetime import date
from typing import Any, Dict

from src.adapters.base import UIRenderer
from src.adapters.normalized import NormalizedInteraction
from src.models import MealType, UserRole
from src.services.meal_service import meal_service, MEAL_DISPLAY, DEFAULT_MEAL_TYPES
from src.utils import parse_date_option, validate_date_for_update

logger = logging.getLogger(__name__)

# Custom ID prefix for meal toggle buttons
MEAL_TOGGLE_PREFIX = "meal_toggle"


def handle_meal_update(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    try:
        date_str = interaction.options.get("date")

        try:
            target_date = parse_date_option(date_str)
        except ValueError as e:
            return renderer.render_error(str(e))

        is_valid, error_msg = validate_date_for_update(target_date)
        if not is_valid:
            return renderer.render_error(error_msg)

        # Google Chat text-based toggle: /meal-update lunch or /meal-update snacks
        args = interaction.options.get("_args", [])
        if args and interaction.platform == "google_chat":
            meal_arg = args[0].lower()
            try:
                meal_type = MealType(meal_arg)
            except ValueError:
                return renderer.render_error(
                    f"Unknown meal type: **{meal_arg}**. Use {', '.join(f'`{m.value}`' for m in DEFAULT_MEAL_TYPES)}."
                )
            success, result = meal_service.toggle_meal_participation(
                discord_id=interaction.user.user_id,
                target_date=target_date,
                meal_type=meal_type,
                updated_by=interaction.user.user_id,
                team=interaction.user.team,
            )
            if not success:
                return renderer.render_error(result)
            meal_record = result
            status = "opted in" if meal_record.is_participating else "opted out"
            display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
            confirmation = f"✅ {display['emoji']} {display['label']}: {status}"
            meals = meal_service.get_user_meals_for_date(interaction.user.user_id, target_date)
            return renderer.render_meal_status(
                interaction.user.user_id, target_date, meals,
                confirmation=confirmation, team=interaction.user.team,
            )

        meals = meal_service.get_user_meals_for_date(interaction.user.user_id, target_date)
        return renderer.render_meal_status(interaction.user.user_id, target_date, meals, team=interaction.user.team)

    except Exception as e:
        logger.exception(f"Error handling meal-update: {e}")
        return renderer.render_error("An error occurred while fetching your meal status. Please try again.")


def handle_meal_toggle(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    try:
        action_id = interaction.action_id or ""

        # Parse action_id: meal_toggle:<user_id>:<date>:<meal_type>
        parts = action_id.split(":")
        if len(parts) != 4 or parts[0] != MEAL_TOGGLE_PREFIX:
            return renderer.render_error("Invalid button interaction.")

        _, target_user_id, date_str, meal_type_str = parts

        # Security: ensure the clicking user matches the button target
        if interaction.user.user_id != target_user_id:
            return renderer.render_error("You can only update your own meal participation.")

        target_date = date.fromisoformat(date_str)
        meal_type = MealType(meal_type_str)

        success, result = meal_service.toggle_meal_participation(
            discord_id=interaction.user.user_id,
            target_date=target_date,
            meal_type=meal_type,
            updated_by=interaction.user.user_id,
            team=interaction.user.team,
        )

        if not success:
            return renderer.render_error(result)

        # Rebuild status with confirmation
        updated_meals = meal_service.get_user_meals_for_date(interaction.user.user_id, target_date)
        display = meal_service.get_meal_display_info(meal_type)
        status_text = "✅ Opted In" if result.is_participating else "❌ Opted Out"
        confirmation = (
            f"Updated **{display['emoji']} {display['label']}** → {status_text}\n\n"
            f"Click a button below to toggle your participation for each meal."
        )

        status = renderer.render_meal_status(interaction.user.user_id, target_date, updated_meals, confirmation, team=interaction.user.team)
        return renderer.render_update(status)

    except Exception as e:
        logger.exception(f"Error handling meal toggle: {e}")
        return renderer.render_error("An error occurred while updating your meal status. Please try again.")


# ── Feature Lambda entry point ────────────────────────────────────────────────

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    from src.adapters.discord.renderer import DiscordRenderer
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

        normalized = NormalizedInteraction(
            platform=user_dict.get("platform", "discord"),
            interaction_type=event["dispatch_type"],
            command_name=event.get("command_name"),
            action_id=event.get("action_id") or event.get("interaction", {}).get("data", {}).get("custom_id"),
            options=event.get("options") or _extract_options_from_raw(event.get("interaction", {})),
            raw_body=event.get("interaction", {}),
            user=user,
        )
    except KeyError as e:
        logger.error("Malformed dispatch event, missing key: %s", e)
        return renderer.render_error(f"Internal error: missing required field {e}")

    if event["dispatch_type"] == "command":
        return handle_meal_update(normalized, renderer)
    else:
        return handle_meal_toggle(normalized, renderer)


def _extract_options_from_raw(interaction: Dict[str, Any]) -> Dict[str, Any]:
    data = interaction.get("data", {})
    options_list = data.get("options", [])
    return {opt["name"]: opt["value"] for opt in options_list}
