import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

from src.adapters.normalized import NormalizedInteraction

if TYPE_CHECKING:
    from src.handlers.auth import AuthenticatedUser

logger = logging.getLogger(__name__)


class GoogleChatIngressAdapter:

    def normalize(
        self,
        body: Dict[str, Any],
        user: "AuthenticatedUser",
    ) -> Optional[NormalizedInteraction]:
        chat = body.get("chat") or {}

        # ── New API format: slash command ──────────────────────────────────────
        app_cmd = chat.get("appCommandPayload")
        if app_cmd:
            message = app_cmd.get("message") or {}
            text = message.get("text", "").strip()
            if text.startswith("/"):
                command_name = text[1:].split()[0]
                raw_args = text[len(command_name) + 1:].strip()
                options = _parse_text_options(raw_args)
                return NormalizedInteraction(
                    platform="google_chat",
                    interaction_type="command",
                    command_name=command_name,
                    action_id=None,
                    options=options,
                    raw_body=body,
                    user=user,
                )
            logger.warning("Google Chat APP_COMMAND text does not start with '/': %r", text)
            return None

        

def _parse_text_options(raw_args: str) -> Dict[str, Any]:
    options: Dict[str, Any] = {}
    for token in raw_args.split():
        if ":" in token:
            key, _, value = token.partition(":")
            options[key.strip()] = value.strip()
    return options
