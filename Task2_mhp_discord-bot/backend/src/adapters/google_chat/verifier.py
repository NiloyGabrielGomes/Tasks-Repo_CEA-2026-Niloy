import base64
import json
import logging
from typing import Any, Dict, Optional

from src.adapters.base import InteractionVerifier
from src.config import settings

logger = logging.getLogger(__name__)


class GoogleChatVerifier(InteractionVerifier):

    def verify(self, raw_event: Dict[str, Any]) -> bool:
        if not settings.ENABLE_GOOGLE_CHAT:
            return False

        headers = raw_event.get("headers") or {}
        auth_header = headers.get("Authorization") or headers.get("authorization", "")
        token = auth_header.removeprefix("Bearer ").strip()

        if not token:
            logger.error("Google Chat: missing Authorization bearer token")
            return False

        project_number = settings.GOOGLE_CHAT_AUDIENCE
        if not project_number:
            logger.error("GOOGLE_CHAT_AUDIENCE not configured")
            return False

        return _verify_jwt(token, project_number)

    def extract_body(self, raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        body = raw_event.get("body", "")
        try:
            if raw_event.get("isBase64Encoded"):
                body = base64.b64decode(body).decode("utf-8")
            return json.loads(body)
        except Exception as e:
            logger.error(f"Google Chat: failed to parse request body: {e}")
            return None


def _verify_jwt(token: str, audience: str) -> bool:
    try:
        from google.oauth2 import id_token
        from google.auth.transport.requests import Request as GoogleRequest
        id_token.verify_oauth2_token(token, GoogleRequest(), audience=audience)
        return True
    except Exception as e:
        print(f"[DEBUG] JWT verify failed: {e} | audience={audience}")
        logger.error(f"Google Chat JWT verification failed: {e}")
        return False
