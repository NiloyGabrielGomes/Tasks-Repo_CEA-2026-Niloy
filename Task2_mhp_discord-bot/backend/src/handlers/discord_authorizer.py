import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def _normalize_headers(event: Dict[str, Any]) -> Dict[str, str]:
    headers = event.get("headers") or {}
    return {str(key).lower(): str(value) for key, value in headers.items() if value is not None}


def _deny(reason: str) -> Dict[str, Any]:
    logger.warning("Discord authorizer denied request: %s", reason)
    return {"isAuthorized": False, "context": {"reason": reason, "platform": "discord"}}


def _allow(context: Dict[str, str]) -> Dict[str, Any]:
    return {"isAuthorized": True, "context": context}


def _is_discord_path(http_path: str) -> bool:
    return http_path == "/discord" or http_path.endswith("/discord")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    headers = _normalize_headers(event)
    route_key = (
        event.get("routeKey")
        or event.get("requestContext", {}).get("routeKey")
        or ""
    )
    http_method = (
        event.get("requestContext", {})
        .get("http", {})
        .get("method")
        or event.get("httpMethod")
        or ""
    )
    http_path = (
        event.get("requestContext", {})
        .get("http", {})
        .get("path")
        or event.get("rawPath")
        or event.get("path")
        or ""
    )

    if http_method.upper() != "POST":
        return _deny("only POST requests are allowed")

    if http_path and not _is_discord_path(http_path):
        return _deny(f"unexpected path: {http_path}")

    if route_key and route_key.upper() != "POST /DISCORD":
        return _deny(f"unexpected route: {route_key}")

    signature = headers.get("x-signature-ed25519", "")
    timestamp = headers.get("x-signature-timestamp", "")
    content_type = headers.get("content-type", "")

    if not signature or not timestamp:
        return _deny("missing Discord signature headers")

    if content_type and "application/json" not in content_type.lower():
        return _deny(f"unexpected content-type: {content_type}")

    return _allow(
        {
            "platform": "discord",
            "route": "/discord",
            "method": "POST",
        }
    )