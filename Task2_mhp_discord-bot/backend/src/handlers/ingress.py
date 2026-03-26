import json
import logging
from typing import Any, Dict

from src.adapters.discord.verifier import DiscordVerifier
from src.adapters.discord.auth_adapter import DiscordUserResolver
from src.adapters.discord.ingress_adapter import DiscordIngressAdapter, INTERACTION_PING
from src.adapters.discord.renderer import DiscordRenderer
from src.handlers.auth import check_command_authorization
from src.models import User
from src.storage.dynamodb import storage as _db
from src.handlers.meal_handler import (
    handle_meal_update,
    handle_meal_toggle,
    MEAL_TOGGLE_PREFIX,
)
from src.handlers.location_handler import (
    handle_work_location,
    handle_location_set,
    LOCATION_SET_PREFIX,
)
from src.handlers.override_handler import (
    handle_override_update,
    handle_override_meal,
    handle_override_location,
    OVERRIDE_MEAL_PREFIX,
    OVERRIDE_LOC_PREFIX,
)
from src.handlers.link_handler import handle_link_identity
from src.handlers.headcount_handler import handle_team_summary, handle_headcount_summary
from src.handlers import dispatcher
from src.config import settings

logger = logging.getLogger(__name__)

# Discord interaction types
INTERACTION_APPLICATION_COMMAND = 2
INTERACTION_MESSAGE_COMPONENT = 3

# Discord response types
RESPONSE_PONG = 1
RESPONSE_CHANNEL_MESSAGE = 4

# Module-level adapter singletons (reused across warm Lambda invocations)
_verifier = DiscordVerifier()
_resolver = DiscordUserResolver()
_ingress_adapter = DiscordIngressAdapter()
_renderer = DiscordRenderer()


def _serialize_user(user) -> Dict[str, Any]:
    return {
        "user_id": user.user_id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role.value,
        "team": user.team,
        "space_id": user.space_id,
        "platform_roles": user.platform_roles,
        "platform": user.platform,
    }


def create_error_response(message: str) -> Dict[str, Any]:
    return {
        "type": RESPONSE_CHANNEL_MESSAGE,
        "data": {"content": f"❌ {message}", "flags": 64},
    }


# ── In-process routing (fallback path) ───────────────────────────────────────

def _route_inprocess(normalized, interaction_type: int) -> Dict[str, Any]:
    if interaction_type == INTERACTION_APPLICATION_COMMAND:
        cmd = normalized.command_name or ""
        logger.info(f"In-process routing command: {cmd}")
        if cmd == "meal-update":
            return handle_meal_update(normalized, _renderer)
        if cmd == "work-location":
            return handle_work_location(normalized, _renderer)
        if cmd == "override-update":
            return handle_override_update(normalized, _renderer)
        if cmd == "link-identity":
            return handle_link_identity(normalized, _renderer)
        if cmd == "team-summary":
            return handle_team_summary(normalized, _renderer)
        if cmd == "headcount-summary":
            return handle_headcount_summary(normalized, _renderer)
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {
                "content": f"🔧 Command `{cmd}` is being implemented. Stay tuned!\n\nYour role: {normalized.user.role.value}",
                "flags": 64,
            },
        }
    else:  # MESSAGE_COMPONENT
        aid = normalized.action_id or ""
        if aid.startswith(MEAL_TOGGLE_PREFIX):
            return handle_meal_toggle(normalized, _renderer)
        if aid.startswith(LOCATION_SET_PREFIX):
            return handle_location_set(normalized, _renderer)
        if aid.startswith(OVERRIDE_MEAL_PREFIX):
            return handle_override_meal(normalized, _renderer)
        if aid.startswith(OVERRIDE_LOC_PREFIX):
            return handle_override_location(normalized, _renderer)
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {"content": "🔧 Component interactions are being implemented.", "flags": 64},
        }


# ── Multi-Lambda dispatch path ────────────────────────────────────────────────

def _dispatch(normalized, interaction_type: int) -> Dict[str, Any]:
    if interaction_type == INTERACTION_APPLICATION_COMMAND:
        cmd = normalized.command_name or ""
        fn = dispatcher.get_function_for_command(cmd)
        if not fn:
            logger.warning(f"No feature Lambda for command: {cmd}")
            return _route_inprocess(normalized, interaction_type)
        payload = {
            "dispatch_type": "command",
            "command_name": cmd,
            "options": normalized.options,
            "interaction": normalized.raw_body,
            "user": _serialize_user(normalized.user),
        }
    else:  # MESSAGE_COMPONENT
        aid = normalized.action_id or ""
        fn = dispatcher.get_function_for_component(aid)
        if not fn:
            logger.warning(f"No feature Lambda for component: {aid}")
            return _route_inprocess(normalized, interaction_type)
        payload = {
            "dispatch_type": "component",
            "action_id": aid,
            "interaction": normalized.raw_body,
            "user": _serialize_user(normalized.user),
        }

    result = dispatcher.dispatch(fn, payload, async_mode=False)
    if result is None:
        return create_error_response("Feature Lambda returned no response.")
    return result


# ── Lambda entry point ────────────────────────────────────────────────────────

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info(f"Received event: {event.get('httpMethod')} {event.get('path')}")

    try:
        if not _verifier.verify(event):
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "Invalid signature"}),
            }

        body = _verifier.extract_body(event)
        if not body:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Failed to parse request body"}),
            }

        interaction_type = body.get("type")

        if interaction_type == INTERACTION_PING:
            logger.info("Responding to PING")
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"type": RESPONSE_PONG}),
            }

        user = _resolver.resolve(body)
        logger.info(f"User authenticated: {user.username} ({user.user_id}), role: {user.role.value}")
        _db.upsert_user(User(
            user_id=user.user_id,
            name=user.display_name or user.username,
            role=user.role,
            team=user.team,
        ))

        normalized = _ingress_adapter.normalize(body, user)
        if not normalized:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(create_error_response(f"Unknown interaction type: {interaction_type}")),
            }

        # Authorization check for commands
        if normalized.interaction_type == "command" and normalized.command_name:
            is_authorized, error_msg = check_command_authorization(normalized.command_name, user)
            if not is_authorized:
                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(create_error_response(error_msg)),
                }

        if settings.ENABLE_MULTI_LAMBDA:
            response = _dispatch(normalized, interaction_type)
        else:
            response = _route_inprocess(normalized, interaction_type)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response),
        }

    except Exception as e:
        logger.exception(f"Error handling interaction: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(create_error_response("An error occurred processing your request")),
        }
