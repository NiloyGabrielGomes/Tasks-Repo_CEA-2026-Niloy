import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

from src.adapters.normalized import NormalizedInteraction

if TYPE_CHECKING:
    from src.handlers.auth import AuthenticatedUser

logger = logging.getLogger(__name__)

INTERACTION_PING = 1
INTERACTION_APPLICATION_COMMAND = 2
INTERACTION_MESSAGE_COMPONENT = 3


class DiscordIngressAdapter:

    def normalize(
        self,
        body: Dict[str, Any],
        user: "AuthenticatedUser",
    ) -> Optional[NormalizedInteraction]:
        interaction_type = body.get("type")

        if interaction_type == INTERACTION_APPLICATION_COMMAND:
            data = body.get("data", {})
            options = _parse_command_options(data)
            return NormalizedInteraction(
                platform="discord",
                interaction_type="command",
                command_name=data.get("name", ""),
                action_id=None,
                options=options,
                raw_body=body,
                user=user,
            )

        elif interaction_type == INTERACTION_MESSAGE_COMPONENT:
            data = body.get("data", {})
            return NormalizedInteraction(
                platform="discord",
                interaction_type="action",
                command_name=None,
                action_id=data.get("custom_id", ""),
                options={},
                raw_body=body,
                user=user,
            )

        else:
            logger.warning(f"DiscordIngressAdapter: unhandled interaction type {interaction_type}")
            return None


def _parse_command_options(data: Dict[str, Any]) -> Dict[str, Any]:
    options_list = data.get("options", [])
    resolved = data.get("resolved", {})
    result: Dict[str, Any] = {}

    for opt in options_list:
        result[opt["name"]] = opt["value"]
        if opt.get("type") == 6:  # USER option type
            user_id_val = opt["value"]
            if user_id_val in resolved.get("users", {}):
                result[f"_resolved_user_{opt['name']}"] = resolved["users"][user_id_val]
            if user_id_val in resolved.get("members", {}):
                result[f"_resolved_member_{opt['name']}"] = resolved["members"][user_id_val]

    return result
