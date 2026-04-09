# Handles /policy view and /policy set slash commands
import json
import logging
from typing import Any, Dict

from src.adapters.base import UIRenderer
from src.adapters.normalized import NormalizedInteraction
from src.services.policy_service import (
    POLICY_KEYS,
    get_all_policies,
    set_policy,
    validate_policy_value,
)

logger = logging.getLogger(__name__)


def handle_policy(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    """Top-level dispatcher: routes to view or set based on subcommand."""
    # Discord: subcommand stored in _subcommand by ingress adapter
    subcommand = interaction.options.get("_subcommand")

    # Google Chat: /policy view or /policy set cutoff-time 22:00
    if not subcommand:
        args = interaction.options.get("_args", [])
        subcommand = args[0] if args else "view"

    if subcommand == "set":
        return handle_policy_set(interaction, renderer)
    return handle_policy_view(interaction, renderer)


def handle_policy_view(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    try:
        policies = get_all_policies()
        return renderer.render_policy_view(policies)
    except Exception as e:
        logger.exception("Error handling policy view: %s", e)
        return renderer.render_error(
            "An error occurred while fetching policy settings. Please try again."
        )


def handle_policy_set(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    try:
        # Discord subcommand options
        setting = interaction.options.get("setting")
        value = interaction.options.get("value")

        # Google Chat: /policy set cutoff-time 22:00
        if not setting:
            args = interaction.options.get("_args", [])
            # args[0] = "set", args[1] = setting name, args[2+] = value
            if len(args) >= 3:
                setting = args[1]
                value = " ".join(args[2:])
            elif len(args) == 2:
                setting = args[1]

        if not setting:
            return renderer.render_error(
                "Please specify a setting to update. "
                f"Valid settings: {', '.join(f'`{k}`' for k in POLICY_KEYS)}."
            )

        # Normalize hyphens to underscores (cutoff-time → cutoff_time)
        setting = setting.replace("-", "_")

        if setting not in POLICY_KEYS:
            return renderer.render_error(
                f"Unknown policy: `{setting}`. "
                f"Valid policies: {', '.join(f'`{k}`' for k in POLICY_KEYS)}."
            )

        if not value:
            return renderer.render_error(
                f"Please provide a value for `{setting}`."
            )

        # Get old value for confirmation display
        old_policies = get_all_policies()
        old_value = old_policies.get(setting, "")

        # Validate the new value
        is_valid, error_msg = validate_policy_value(setting, value)
        if not is_valid:
            return renderer.render_error(error_msg)

        # For active_meal_types, store as JSON array
        if setting == "active_meal_types":
            types = [t.strip() for t in value.split(",") if t.strip()]
            value = json.dumps(types)

        set_policy(setting, value)

        # Format display value for confirmation
        display_value = value
        if setting == "active_meal_types":
            display_value = ", ".join(json.loads(value))

        return renderer.render_policy_set_confirmation(setting, old_value, display_value)

    except Exception as e:
        logger.exception("Error handling policy set: %s", e)
        return renderer.render_error(
            "An error occurred while updating the policy. Please try again."
        )
