# Handles /team-summary and /headcount-summary slash commands
import logging
from datetime import date
from typing import Any, Dict

from src.adapters.base import UIRenderer
from src.adapters.normalized import NormalizedInteraction
from src.models import UserRole
from src.services.headcount_service import headcount_service
from src.utils import get_dhaka_today

logger = logging.getLogger(__name__)


def handle_team_summary(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    try:
        date_str = interaction.options.get("date")
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                return renderer.render_error(
                    f"Invalid date format: '{date_str}'. Use YYYY-MM-DD."
                )
        else:
            target_date = get_dhaka_today()

        # Team leads see their own team; admins can optionally specify a different team
        team_name = interaction.options.get("team") or interaction.user.team
        if not team_name:
            return renderer.render_error(
                "You are not assigned to a team. Ask an admin to assign you to a team."
            )

        summary = headcount_service.get_team_summary(target_date, team_name)
        return renderer.render_team_summary(target_date, team_name, summary)

    except Exception as e:
        logger.exception(f"Error handling team-summary: {e}")
        return renderer.render_error(
            "An error occurred while fetching the team summary. Please try again."
        )


def handle_headcount_summary(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    try:
        date_str = interaction.options.get("date")
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                return renderer.render_error(
                    f"Invalid date format: '{date_str}'. Use YYYY-MM-DD."
                )
        else:
            target_date = get_dhaka_today()

        team_filter = interaction.options.get("team") or None

        summary = headcount_service.get_headcount_summary(target_date, team_filter)
        return renderer.render_headcount_summary(target_date, summary, team_filter)

    except Exception as e:
        logger.exception(f"Error handling headcount-summary: {e}")
        return renderer.render_error(
            "An error occurred while fetching the headcount summary. Please try again."
        )


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
        action_id=None,
        options=event.get("options", {}),
        raw_body=event.get("interaction", {}),
        user=user,
    )

    cmd = event.get("command_name", "")
    if cmd == "team-summary":
        return handle_team_summary(normalized, renderer)
    return handle_headcount_summary(normalized, renderer)
