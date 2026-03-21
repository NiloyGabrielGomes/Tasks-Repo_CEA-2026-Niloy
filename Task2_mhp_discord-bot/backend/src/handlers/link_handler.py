# Handles /link-identity slash command (Discord and Google Chat)
#
# Scope rules:
#   Admin     → can link any employee (provide employee mention / google_email freely)
#   Team Lead → can only link themselves
#   Employee  → can only link themselves
#
# Discord:  /link-identity employee:<@mention>  google_email:<email>
#   - employee option is optional; omitting it means "myself"
#
# Google Chat: /link-identity discord_id:<snowflake>  google_email:<email>
#   - google_email option is optional; omitting it means "myself" (actor's email)
import logging
from typing import Any, Dict

from src.adapters.base import UIRenderer
from src.adapters.normalized import NormalizedInteraction
from src.models import ExternalIdentity, UserRole
from src.storage.dynamodb import storage

logger = logging.getLogger(__name__)


def handle_link_identity(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    try:
        if interaction.user.platform == "google_chat":
            return _handle_google_chat_link(interaction, renderer)
        return _handle_discord_link(interaction, renderer)
    except Exception as e:
        logger.exception("Error handling link-identity: %s", e)
        return renderer.render_error("An error occurred while linking identities. Please try again.")


# ── Discord path ──────────────────────────────────────────────────────────────

def _handle_discord_link(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    actor = interaction.user
    options = interaction.options

    google_email = (options.get("google_email") or "").strip().lower()
    if not google_email:
        return renderer.render_error(
            "Please provide the Google Chat email address using the `google_email` option."
        )

    # employee option is the Discord snowflake of the target user (from mention)
    target_discord_id = options.get("employee") or actor.user_id

    # Scope check: non-admins can only link themselves
    if actor.role != UserRole.ADMIN and target_discord_id != actor.user_id:
        return renderer.render_error(
            "You can only link your own identity. Admins can link any employee."
        )

    _write_identity_pair(discord_id=target_discord_id, google_email=google_email)

    logger.info(
        "Identity linked via Discord: discord=%s ↔ google_chat=%s  (by actor=%s)",
        target_discord_id, google_email, actor.user_id,
    )

    if target_discord_id == actor.user_id:
        msg = f"Your Discord account is now linked to Google Chat email **{google_email}**."
    else:
        msg = f"<@{target_discord_id}> is now linked to Google Chat email **{google_email}**."

    return renderer.render_success(msg)


# ── Google Chat path ──────────────────────────────────────────────────────────

def _handle_google_chat_link(
    interaction: NormalizedInteraction,
    renderer: UIRenderer,
) -> Dict[str, Any]:
    actor = interaction.user
    options = interaction.options

    discord_id = (options.get("discord_id") or "").strip()
    if not discord_id:
        return renderer.render_error(
            "Please provide the Discord user ID using the `discord_id` option "
            "(e.g. `/link-identity discord_id:111222333`)."
        )

    # google_email defaults to the actor's own email when not provided
    google_email = (options.get("google_email") or actor.username or "").strip().lower()
    if not google_email:
        return renderer.render_error(
            "Could not determine the Google Chat email. Please provide it explicitly "
            "using the `google_email` option."
        )

    # Scope check: non-admins can only link their own Google Chat email
    if actor.role != UserRole.ADMIN and google_email != (actor.username or "").lower():
        return renderer.render_error(
            "You can only link your own identity. Admins can link any employee."
        )

    _write_identity_pair(discord_id=discord_id, google_email=google_email)

    logger.info(
        "Identity linked via Google Chat: discord=%s ↔ google_chat=%s  (by actor=%s)",
        discord_id, google_email, actor.user_id,
    )

    if google_email == (actor.username or "").lower():
        msg = f"Your Google Chat account is now linked to Discord ID **{discord_id}**."
    else:
        msg = f"Google Chat email **{google_email}** is now linked to Discord ID **{discord_id}**."

    return renderer.render_success(msg)


# ── Shared write ──────────────────────────────────────────────────────────────

def _write_identity_pair(discord_id: str, google_email: str) -> None:
    """Write both IDENT items using the Discord snowflake as the canonical user_id."""
    storage.put_identity(ExternalIdentity(
        provider="discord",
        external_id=discord_id,
        user_id=discord_id,
    ))
    storage.put_identity(ExternalIdentity(
        provider="google_chat",
        external_id=google_email,
        user_id=discord_id,
    ))
