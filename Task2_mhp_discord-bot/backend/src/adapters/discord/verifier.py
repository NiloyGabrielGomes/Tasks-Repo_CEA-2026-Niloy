import base64
import json
import logging
import os
from typing import Any, Dict, Optional

from nacl.signing import VerifyKey
from nacl.encoding import RawEncoder

from src.adapters.base import InteractionVerifier
from src.config import settings

logger = logging.getLogger(__name__)


class DiscordVerifier(InteractionVerifier):

    def verify(self, raw_event: Dict[str, Any]) -> bool:
        headers = raw_event.get("headers", {}) or {}
        signature = headers.get("X-Signature-Ed25519") or headers.get("x-signature-ed25519")
        timestamp = headers.get("X-Signature-Timestamp") or headers.get("x-signature-timestamp")
        body = raw_event.get("body", "")

        if settings.DEBUG and os.getenv("SKIP_SIGNATURE_VERIFICATION"):
            logger.warning("Signature verification skipped (DEBUG mode)")
            return True

        if not signature or not timestamp:
            logger.error("Missing Discord signature or timestamp headers")
            return False

        return _verify_signature(body, signature, timestamp)

    def extract_body(self, raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        body = raw_event.get("body", "")
        try:
            if raw_event.get("isBase64Encoded"):
                body = base64.b64decode(body).decode("utf-8")
            return json.loads(body)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse Discord request body: {e}")
            return None


def _verify_signature(event_body: str, signature: str, timestamp: str) -> bool:
    try:
        public_key = settings.DISCORD_PUBLIC_KEY
        if not public_key:
            logger.error("DISCORD_PUBLIC_KEY not configured")
            return False
        verify_key = VerifyKey(bytes.fromhex(public_key))
        message = timestamp.encode() + event_body.encode()
        verify_key.verify(message, bytes.fromhex(signature), encoder=RawEncoder)
        return True
    except Exception as e:
        logger.error(f"Discord signature verification failed: {e}")
        return False
