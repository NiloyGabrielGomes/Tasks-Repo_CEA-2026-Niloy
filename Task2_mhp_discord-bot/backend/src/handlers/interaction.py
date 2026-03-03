#Discord Interaction Handler
import json
import logging
import os
from typing import Any, Dict, Optional

from nacl.signing import VerifyKey
from nacl.encoding import RawEncoder

from src.config import settings
from src.services.discord_helpers import extract_team_from_roles

from src.handlers.auth import (
    AuthenticatedUser,
    get_user_from_interaction as auth_get_user,
    check_command_authorization,
)
from src.models import UserRole

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
    roles = member.get("roles", [])
    
    return {
        "id": member.get("user", {}).get("id") or user.get("id", ""),
        "username": member.get("user", {}).get("username") or user.get("username", ""),
        "global_name": member.get("user", {}).get("global_name") or user.get("global_name"),
        "roles": roles,
        "team": extract_team_from_roles(roles),
        "guild_id": member.get("guild_id") or interaction.get("guild_id", ""),
    }


def get_command_name(interaction: Dict[str, Any]) -> str:

    data = interaction.get("data", {})
    return data.get("name", "")


def create_error_response(message: str) -> Dict[str, Any]:

    return {
        "type": RESPONSE_CHANNEL_MESSAGE,
        "data": {
            "content": f"❌ {message}",
            "flags": 64  # Ephemeral - only user sees it
        }
    }


def route_command(interaction: Dict[str, Any], user: AuthenticatedUser) -> Dict[str, Any]:

    command_name = get_command_name(interaction)
    
    logger.info(f"Routing command: {command_name} for user: {user.discord_id}")
    
    # Check authorization
    is_authorized, error_msg = check_command_authorization(command_name, user)
    if not is_authorized:
        return create_error_response(error_msg)
    
    # Placeholder response - feature handlers will be added in subsequent issues
    return {
        "type": RESPONSE_CHANNEL_MESSAGE,
        "data": {
            "content": f"🔧 Command `{command_name}` is being implemented. Stay tuned!\n\nYour role: {user.role.value}",
            "flags": 64  # Ephemeral
        }
    }


def handle_component_interaction(interaction: Dict[str, Any], user: AuthenticatedUser) -> Dict[str, Any]:
    return {
        "type": RESPONSE_CHANNEL_MESSAGE,
        "data": {
            "content": "🔧 Component interactions are being implemented. Stay tuned!",
            "flags": 64
        }
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    
    logger.info(f"Received event: {event.get('httpMethod')} {event.get('path')}")
    
    try:
        interaction = parse_interaction(event)
        
        if not interaction:
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "Invalid signature"})
            }
        
        # Handle PING (Discord verification)
        interaction_type = interaction.get("type")
        
        if interaction_type == INTERACTION_PING:
            logger.info("Responding to PING")
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"type": RESPONSE_PONG})
            }
        
        # Use auth module to get authenticated user with role
        user = auth_get_user(interaction)
        
        logger.info(f"User authenticated: {user.username} ({user.discord_id}), role: {user.role.value}")
        
        # Route to appropriate handler based on interaction type
        if interaction_type == INTERACTION_APPLICATION_COMMAND:
            response = route_command(interaction, user)
        elif interaction_type == INTERACTION_MESSAGE_COMPONENT:
            response = handle_component_interaction(interaction, user)
        else:
            response = create_error_response(f"Unknown interaction type: {interaction_type}")
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response)
        }
        
    except Exception as e:
        logger.exception(f"Error handling interaction: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(create_error_response("An error occurred processing your request"))
        }
