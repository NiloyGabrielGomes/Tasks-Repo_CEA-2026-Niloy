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

        # ── New API format: card/button click (check BEFORE appCommandPayload) ──
        # Google Chat includes appCommandPayload as context in button click events,
        # so buttonClickedPayload must be checked first to avoid misclassification.
        btn_payload = chat.get("buttonClickedPayload")
        if btn_payload:
            action = btn_payload.get("action") or {}
            params = {p["key"]: p["value"] for p in action.get("parameters", [])}
            # Dialog buttons use action.function; legacy buttons use action_id in parameters
            action_id = (
                params.get("action_id")
                or action.get("function", "")
                or action.get("actionMethodName", "")
            )
            # Parse dialog form values if present
            form_values = _extract_dialog_form_values(btn_payload)
            if form_values:
                params.update(form_values)
            return NormalizedInteraction(
                platform="google_chat",
                interaction_type="action",
                command_name=None,
                action_id=action_id,
                options=params,
                raw_body=body,
                user=user,
            )

        # ── New API format: slash command ──────────────────────────────────────
        app_cmd = chat.get("appCommandPayload")
        if app_cmd:
            message = app_cmd.get("message") or {}
            text = message.get("text", "").strip()
            if text.startswith("/"):
                command_name = text[1:].split()[0]
                raw_args = text[len(command_name) + 1:].strip()
                options = _parse_text_options(raw_args)
                _enrich_with_mentions(options, message)
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

        # ── Legacy API format ──────────────────────────────────────────────────
        event_type = body.get("type", "")

        if event_type in ("MESSAGE", "APP_COMMAND"):
            message = body.get("message") or {}
            text = message.get("text", "").strip()
            arg_text = message.get("argumentText", "").strip()
            if text.startswith("/"):
                command_name = text[1:].split()[0]
                options = _parse_text_options(arg_text or text[len(command_name) + 1:].strip())
                _enrich_with_mentions(options, message)
                return NormalizedInteraction(
                    platform="google_chat",
                    interaction_type="command",
                    command_name=command_name,
                    action_id=None,
                    options=options,
                    raw_body=body,
                    user=user,
                )
            logger.warning("Google Chat %s text does not start with '/': %r", event_type, text)
            return None

        if event_type == "CARD_CLICKED":
            action = body.get("action") or {}
            params = {p["key"]: p["value"] for p in action.get("parameters", [])}
            action_id = (
                params.get("action_id")
                or action.get("function", "")
                or action.get("actionMethodName", "")
            )
            form_values = _extract_dialog_form_values(body)
            if form_values:
                params.update(form_values)
            return NormalizedInteraction(
                platform="google_chat",
                interaction_type="action",
                command_name=None,
                action_id=action_id,
                options=params,
                raw_body=body,
                user=user,
            )

        logger.warning("GoogleChatIngressAdapter: unhandled event type: %r  body keys: %s",
                       event_type, list(body.keys()))
        return None


def _parse_text_options(raw_args: str) -> Dict[str, Any]:
    options: Dict[str, Any] = {}
    positional = []
    for token in raw_args.split():
        if ":" in token:
            key, _, value = token.partition(":")
            options[key.strip()] = value.strip()
        else:
            positional.append(token)
    # Store positional args so handlers can use them (e.g. "/meal-update lunch")
    if positional:
        options["_args"] = positional
    return options


def _enrich_with_mentions(options: Dict[str, Any], message: Dict[str, Any]) -> None:
    annotations = message.get("annotations") or []
    for ann in annotations:
        if ann.get("type") != "USER_MENTION":
            continue
        mention_user = (ann.get("userMention") or {}).get("user") or {}
        mention_email = mention_user.get("email", "")
        mention_id = mention_user.get("name", "")  # e.g. "users/12345"
        mention_display = mention_user.get("displayName", "")

        # If employee is already set to an email, don't overwrite
        employee_val = options.get("employee", "")
        if "@" in employee_val and "." in employee_val:
            break

        # Use email if available, otherwise fall back to Google Chat user ID
        resolved = mention_email or mention_id
        if resolved:
            options["employee"] = resolved
            if mention_display:
                options["_mention_display_name"] = mention_display
        break  # only use the first user mention


def _extract_dialog_form_values(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract form input values from a Google Chat dialog submit payload.

    Google Chat dialog forms submit values under common.formInputs or
    common.invokedFunction. Returns a flat dict of field_name -> value.
    """
    form_values: Dict[str, Any] = {}
    common = payload.get("common") or {}
    form_inputs = common.get("formInputs") or {}

    for field_name, field_data in form_inputs.items():
        # Each field_data is {"stringInputs": {"value": ["the_value"]}}
        string_inputs = field_data.get("stringInputs") or {}
        values = string_inputs.get("value") or []
        if values:
            form_values[field_name] = values[0]

    # Also capture any invoked function from dialog actions
    invoked_function = common.get("invokedFunction")
    if invoked_function:
        form_values["_invoked_function"] = invoked_function

    return form_values
