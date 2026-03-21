# Handles /work-location slash command and location button interactions
import logging
from datetime import date
from typing import Any, Dict

from src.adapters.base import UIRenderer
from src.adapters.normalized import NormalizedInteraction
from src.models import WorkLocationType, UserRole
from src.services.location_service import location_service
from src.utils import parse_date_option, validate_date_for_update

logger = logging.getLogger(__name__)

# Custom ID prefix for work-location buttons
LOCATION_SET_PREFIX = "location_set"


def handle_work_location(
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

        record = location_service.get_user_location_for_date(interaction.user.user_id, target_date)
        current = location_service.get_current_location(record)
        return renderer.render_location_status(interaction.user.user_id, target_date, current)

    except Exception as e:
        logger.exception("Error handling work-location: %s", e)
        return renderer.render_error("An error occurred while fetching your work location. Please try again.")


def handle_location_set(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    try:
        action_id = interaction.action_id or ""

        # Parse action_id: location_set:<user_id>:<date>:<location>
        parts = action_id.split(":")
        if len(parts) != 4 or parts[0] != LOCATION_SET_PREFIX:
            return renderer.render_error("Invalid button interaction.")

        _, target_user_id, date_str, location_str = parts

        # Security: only the user themselves can click their own buttons
        if interaction.user.user_id != target_user_id:
            return renderer.render_error("You can only update your own work location.")

        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            return renderer.render_error("Invalid date format in button.")

        try:
            location = WorkLocationType(location_str)
        except ValueError:
            return renderer.render_error(f"Unknown location type: {location_str}")

        success, result = location_service.set_work_location(
            discord_id=interaction.user.user_id,
            target_date=target_date,
            location=location,
            updated_by=interaction.user.user_id,
            team=interaction.user.team,
        )

        if not success:
            return renderer.render_error(result)

        loc_display_info = location_service.get_location_display_info(location)
        confirmation = f"Updated → {loc_display_info['emoji']} **{loc_display_info['label']}**"
        status = renderer.render_location_status(
            interaction.user.user_id, target_date, location, confirmation=confirmation
        )
        return renderer.render_update(status)

    except Exception as e:
        logger.exception("Error handling location set: %s", e)
        return renderer.render_error("An error occurred while updating your work location. Please try again.")


# ── Feature Lambda entry point ────────────────────────────────────────────────

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    from src.adapters.discord.renderer import DiscordRenderer
    from src.handlers.auth import AuthenticatedUser

    renderer = DiscordRenderer()
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

    if event["dispatch_type"] == "command":
        return handle_work_location(normalized, renderer)
    else:
        return handle_location_set(normalized, renderer)


def _extract_options_from_raw(interaction: Dict[str, Any]) -> Dict[str, Any]:
    data = interaction.get("data", {})
    options_list = data.get("options", [])
    return {opt["name"]: opt["value"] for opt in options_list}
