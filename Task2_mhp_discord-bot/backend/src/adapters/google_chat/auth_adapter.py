import json
import logging
from typing import Any, Dict, Optional

from src.adapters.base import UserResolver
from src.config import settings
from src.models import UserRole

logger = logging.getLogger(__name__)

# In-memory cache (per Lambda cold start)
_gchat_role_map: dict | None = None


class GoogleChatUserResolver(UserResolver):

    def resolve(self, raw_body: Dict[str, Any]) -> "AuthenticatedUser":
        from src.handlers.auth import AuthenticatedUser
        from src.storage.dynamodb import storage

        chat = raw_body.get("chat") or {}
        user_info = chat.get("user") or raw_body.get("user") or {}
        google_id = user_info.get("name", "")          
        email = user_info.get("email", "")
        display_name = user_info.get("displayName", "")
        app_cmd = chat.get("appCommandPayload") or {}
        space_name = (
            app_cmd.get("space") or
            chat.get("space") or
            raw_body.get("space") or {}
        ).get("name", "")

        canonical_id = storage.get_canonical_user_id("google_chat", email) if email else None
        user_id = canonical_id or google_id

        app_role = _lookup_role(email)
        team = _lookup_team(email)

        logger.info(
            "Google Chat user resolved: %s (%s) - Role: %s - Canonical ID: %s",
            display_name, email, app_role.value,
            canonical_id if canonical_id else "not linked (using Google ID)",
        )

        return AuthenticatedUser(
            user_id=user_id,
            username=email,
            display_name=display_name,
            role=app_role,
            team=team,
            space_id=space_name,
            platform_roles=[],
            platform="google_chat",
        )


# ── Private helpers ───────────────────────────────────────────────────────────

def _get_gchat_role_map() -> dict:
    global _gchat_role_map
    if _gchat_role_map is None:
        from src.storage.dynamodb import storage
        policy = storage.get_policy("google_chat_role_map")
        if policy:
            try:
                _gchat_role_map = json.loads(policy.value)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Invalid google_chat_role_map policy, defaulting to empty")
                _gchat_role_map = {}
        else:
            _gchat_role_map = {}
    return _gchat_role_map


def _lookup_role(email: str) -> UserRole:
    # 1. DynamoDB policy
    role_map = _get_gchat_role_map()
    role_str = role_map.get(email, "")
    if role_str == "admin":
        return UserRole.ADMIN
    if role_str == "team_lead":
        return UserRole.TEAM_LEAD

    # 2. Env var fallback
    admin_emails = [e.strip() for e in settings.GOOGLE_CHAT_ADMIN_EMAILS.split(",") if e.strip()]
    if email in admin_emails:
        return UserRole.ADMIN

    tl_emails = [e.strip() for e in settings.GOOGLE_CHAT_TEAM_LEAD_EMAILS.split(",") if e.strip()]
    if email in tl_emails:
        return UserRole.TEAM_LEAD

    return UserRole.EMPLOYEE


def _lookup_team(email: str) -> Optional[str]:
    role_map = _get_gchat_role_map()
    entry = role_map.get(email)
    if isinstance(entry, dict):
        return entry.get("team")
    return None


def invalidate_gchat_role_cache() -> None:
    global _gchat_role_map
    _gchat_role_map = None
