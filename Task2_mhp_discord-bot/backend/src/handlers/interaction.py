#Discord Interaction Handler
import json
import logging
import os
from typing import Any, Dict, Optional

from nacl.signing import VerifyKey
from nacl.encoding import RawEncoder

from src.config import settings

logger = logging.getLogger(__name__)

# Discord interaction types
INTERACTION_PING = 1
INTERACTION_APPLICATION_COMMAND = 2
INTERACTION_MESSAGE_COMPONENT = 3

# Discord response types
RESPONSE_PONG = 1
RESPONSE_CHANNEL_MESSAGE = 4
RESPONSE_DEFERRED_CHANNEL_MESSAGE = 5
RESPONSE_DEFERRED_UPDATE_MESSAGE = 6
RESPONSE_UPDATE_MESSAGE = 7


def verify_signature(event_body: str, signature: str, timestamp: str) -> bool:
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
        logger.error(f"Signature verification failed: {e}")
        return False


def parse_interaction(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:

    headers = event.get("headers", {}) or {}
    
    signature = headers.get("X-Signature-Ed25519") or headers.get("x-signature-ed25519")
    timestamp = headers.get("X-Signature-Timestamp") or headers.get("x-signature-timestamp")
    
    body = event.get("body", "")
    
    # Verify signature (skip for local development)
    if settings.DEBUG and os.getenv("SKIP_SIGNATURE_VERIFICATION"):
        logger.warning("Signature verification skipped (DEBUG mode)")
    elif not signature or not timestamp:
        logger.error("Missing signature or timestamp headers")
        return None
    elif not verify_signature(body, signature, timestamp):
        logger.error("Invalid signature")
        return None
    
    try:
        if event.get("isBase64Encoded"):
            import base64
            body = base64.b64decode(body).decode("utf-8")
        
        interaction = json.loads(body)
        return interaction
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return None


def get_user_from_interaction(interaction: Dict[str, Any]) -> Dict[str, Any]:
    
    member = interaction.get("member", {})
    user = interaction.get("user", {})
    
    return {
        "id": member.get("user", {}).get("id") or user.get("id", ""),
        "username": member.get("user", {}).get("username") or user.get("username", ""),
        "global_name": member.get("user", {}).get("global_name") or user.get("global_name"),
        "roles": member.get("roles", []),
        "guild_id": member.get("guild_id") or interaction.get("guild_id", ""),
    }


def get_command_name(interaction: Dict[str, Any]) -> str:
    
    data = interaction.get("data", {})
    return data.get("name", "")


