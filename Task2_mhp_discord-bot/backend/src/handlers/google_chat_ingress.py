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
        return {"text": "Google Chat integration not enabled"}

    try:
        verified = _verifier.verify(event)
        if not verified:
            return {"text": "Unauthorized"}

        body = _verifier.extract_body(event)
        if not body:
            return {"text": "Failed to parse request body"}

        user = _resolver.resolve(body)
        logger.info(f"Google Chat user: {user.username} ({user.user_id}), role: {user.role.value}")
        _db.upsert_user(User(
            user_id=user.user_id,
            name=user.display_name or user.username,
            role=user.role,
            team=user.team,
        ))

        normalized = _adapter.normalize(body, user)
        if not normalized:
            return {"text": "Unsupported event type"}

        # Authorization check for commands
        if normalized.interaction_type == "command" and normalized.command_name:
            is_authorized, error_msg = check_command_authorization(normalized.command_name, user)
            if not is_authorized:
                space_name = _extract_space_name(body)
                error_response = _unwrap_render_actions(_renderer.render_error(error_msg))
                _post_to_chat(space_name, error_response)
                return {}

        if normalized.interaction_type == "command":
            response = _route_command(normalized)
        else:
            response = _route_action(normalized)

        if normalized.interaction_type == "action":
            # Button clicks: respond synchronously with UPDATE_MESSAGE
            update_response = _renderer.render_update(response)
            return update_response
        else:
            # Slash commands: post async via Chat REST API, return empty
            # (sync responses don't work with API Gateway v2 + Google Chat)
            space_name = _extract_space_name(body)
            unwrapped = _unwrap_render_actions(response)
            _post_to_chat(space_name, unwrapped)
            return {}

    except Exception as e:
        logger.exception(f"Error handling Google Chat interaction: {e}")
        return {"text": "❌ An error occurred processing your request"}


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
    if cmd == "team-summary":
        return handle_team_summary(normalized, _renderer)
    if cmd == "headcount-summary":
        return handle_headcount_summary(normalized, _renderer)
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


_sa_json_cache: Optional[str] = None


def _get_sa_json_from_ssm() -> Optional[str]:
    """Read service account JSON from SSM Parameter Store (cached across warm invocations)."""
    global _sa_json_cache
    if _sa_json_cache:
        return _sa_json_cache
    try:
        import boto3
        ssm = boto3.client("ssm", region_name="ap-south-1")
        resp = ssm.get_parameter(Name="/mhp/gchat-sa-json", WithDecryption=True)
        _sa_json_cache = resp["Parameter"]["Value"]
        return _sa_json_cache
    except Exception as e:
        logger.error("SSM read failed: %s", e)
        return None


def _get_chat_access_token() -> Optional[str]:
    # Try env var first, then SSM
    sa_json_b64 = settings.GOOGLE_CHAT_SERVICE_ACCOUNT_JSON or _get_sa_json_from_ssm()
    if not sa_json_b64:
        logger.error("No service account JSON available (env or SSM)")
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
    body_bytes = json.dumps(_unwrap_render_actions(message), default=str).encode()
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
    # HTTP API v2 (payload format 2.0): returning a dict without statusCode/body
    # makes API Gateway serialize it as JSON with Content-Type: application/json.
    # The old {statusCode, headers, body} format resulted in text/plain content-type
    # which Google Chat rejects.
    return response
