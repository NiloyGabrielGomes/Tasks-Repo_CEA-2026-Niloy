"""Google Chat Lambda entry point."""
import base64
import json
import logging
import urllib.request
from typing import Any, Dict, Optional

from src.adapters.google_chat.verifier import GoogleChatVerifier
from src.adapters.google_chat.auth_adapter import GoogleChatUserResolver
from src.adapters.google_chat.renderer import GoogleChatRenderer
from src.adapters.google_chat.ingress_adapter import GoogleChatIngressAdapter
from src.handlers.auth import check_command_authorization
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
from src.config import settings

logger = logging.getLogger(__name__)

# Module-level singletons (reused across warm invocations)
_verifier = GoogleChatVerifier()
_resolver = GoogleChatUserResolver()
_renderer = GoogleChatRenderer()
_adapter = GoogleChatIngressAdapter()

_CHAT_SCOPES = ["https://www.googleapis.com/auth/chat.bot"]


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("Google Chat interaction received")

    if not settings.ENABLE_GOOGLE_CHAT:
        return {
            "statusCode": 503,
            "body": json.dumps({"error": "Google Chat integration not enabled"}),
        }

    try:
        if not _verifier.verify(event):
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "Unauthorized"}),
            }

        body = _verifier.extract_body(event)
        if not body:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Failed to parse request body"}),
            }

        user = _resolver.resolve(body)
        logger.info(f"Google Chat user: {user.username} ({user.user_id}), role: {user.role.value}")

        normalized = _adapter.normalize(body, user)
        if not normalized:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Unsupported event type"}),
            }

        # Authorization check for commands
        if normalized.interaction_type == "command" and normalized.command_name:
            is_authorized, error_msg = check_command_authorization(normalized.command_name, user)
            if not is_authorized:
                response = _renderer.render_error(error_msg)
                return _ok(response)

        if normalized.interaction_type == "command":
            response = _route_command(normalized)
        else:
            response = _route_action(normalized)

        if normalized.interaction_type == "action":
            # Button clicks: respond synchronously (Google Chat requires it)
            return _ok(_unwrap_render_actions(response))
        else:
            # Slash commands: respond asynchronously via Chat REST API
            space_name = _extract_space_name(body)
            _post_to_chat(space_name, response)
            return _ok({})

    except Exception as e:
        logger.exception(f"Error handling Google Chat interaction: {e}")
        return _ok({"text": "❌ An error occurred processing your request"})


def _route_command(normalized) -> Dict[str, Any]:
    cmd = normalized.command_name or ""
    if cmd == "meal-update":
        return handle_meal_update(normalized, _renderer)
    if cmd == "work-location":
        return handle_work_location(normalized, _renderer)
    if cmd == "override-update":
        return handle_override_update(normalized, _renderer)
    if cmd == "link-identity":
        return handle_link_identity(normalized, _renderer)
    return _renderer.render_error(f"Unknown command: `{cmd}`")


def _route_action(normalized) -> Dict[str, Any]:
    aid = normalized.action_id or ""
    if aid.startswith(MEAL_TOGGLE_PREFIX):
        return handle_meal_toggle(normalized, _renderer)
    if aid.startswith(LOCATION_SET_PREFIX):
        return handle_location_set(normalized, _renderer)
    if aid.startswith(OVERRIDE_MEAL_PREFIX):
        return handle_override_meal(normalized, _renderer)
    if aid.startswith(OVERRIDE_LOC_PREFIX):
        return handle_override_location(normalized, _renderer)
    return _renderer.render_error("Unknown action")


def _unwrap_render_actions(response: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the inner message dict from a renderActions wrapper, or return as-is."""
    try:
        return response["renderActions"]["hostAppAction"]["chatAction"]["createMessageAction"]["message"]
    except (KeyError, TypeError):
        return response


def _extract_space_name(body: Dict[str, Any]) -> Optional[str]:
    chat = body.get("chat") or {}
    app_cmd = chat.get("appCommandPayload") or {}
    btn = chat.get("buttonClickedPayload") or {}
    space = (
        app_cmd.get("space") or
        btn.get("space") or
        (btn.get("message") or {}).get("space") or
        chat.get("space") or
        body.get("space") or {}
    )
    return space.get("name")


def _get_chat_access_token() -> Optional[str]:
    sa_json_b64 = settings.GOOGLE_CHAT_SERVICE_ACCOUNT_JSON
    if not sa_json_b64:
        logger.error("GOOGLE_CHAT_SERVICE_ACCOUNT_JSON not configured")
        return None
    try:
        from google.oauth2 import service_account
        sa_info = json.loads(base64.b64decode(sa_json_b64 + "==").decode())
        creds = service_account.Credentials.from_service_account_info(
            sa_info, scopes=_CHAT_SCOPES
        )
        creds.refresh(_SimpleRequest())
        return creds.token
    except Exception as e:
        logger.error("Failed to get Chat API access token: %s", e)
        return None


def _post_to_chat(space_name: Optional[str], message: Dict[str, Any]) -> None:
    if not space_name:
        logger.error("No space name — cannot post async message")
        return
    token = _get_chat_access_token()
    if not token:
        return

    url = f"https://chat.googleapis.com/v1/{space_name}/messages"
    body_bytes = json.dumps(_unwrap_render_actions(message)).encode()
    req = urllib.request.Request(
        url,
        data=body_bytes,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info("Posted to Chat API: %s", resp.status)
    except Exception as e:
        logger.error("Failed to post to Chat API: %s", e)


class _SimpleRequest:
    """Minimal google-auth transport Request using stdlib urllib."""
    def __call__(self, url, method="GET", body=None, headers=None, timeout=None, **kwargs):
        req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
        try:
            resp = urllib.request.urlopen(req, timeout=timeout or 30)
            return _SimpleResponse(resp.status, dict(resp.headers), resp.read())
        except urllib.error.HTTPError as e:
            return _SimpleResponse(e.code, {}, e.read())


class _SimpleResponse:
    def __init__(self, status, headers, data):
        self.status = status
        self.headers = headers
        self.data = data


def _ok(response: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response),
    }
