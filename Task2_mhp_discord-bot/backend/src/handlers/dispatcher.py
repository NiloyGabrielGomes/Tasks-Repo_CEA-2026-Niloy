import json
import logging
import os
from typing import Any, Dict, Optional

import boto3

logger = logging.getLogger(__name__)

# ── Command → Lambda function name ───────────────────────────────────────────
COMMAND_FUNCTION_MAP: Dict[str, str] = {
    "meal-update":     os.getenv("MEAL_FUNCTION_NAME", ""),
    "work-location":   os.getenv("LOCATION_FUNCTION_NAME", ""),
    "override-update": os.getenv("OVERRIDE_FUNCTION_NAME", ""),
}

# ── Component custom_id prefix → Lambda function name ────────────────────────
COMPONENT_PREFIX_MAP: Dict[str, str] = {
    "meal_toggle":   os.getenv("MEAL_FUNCTION_NAME", ""),
    "location_set":  os.getenv("LOCATION_FUNCTION_NAME", ""),
    "override_meal": os.getenv("OVERRIDE_FUNCTION_NAME", ""),
    "override_loc":  os.getenv("OVERRIDE_FUNCTION_NAME", ""),
}

def get_function_for_command(command_name: str) -> Optional[str]:
    fn = COMMAND_FUNCTION_MAP.get(command_name)
    return fn if fn else None

def get_function_for_component(custom_id: str) -> Optional[str]:
    for prefix, fn in COMPONENT_PREFIX_MAP.items():
        if custom_id.startswith(prefix):
            return fn if fn else None
    return None

def dispatch(
    function_name: str,
    payload: Dict[str, Any],
    async_mode: bool = False,
) -> Optional[Dict[str, Any]]:
    client = boto3.client("lambda")
    invocation_type = "Event" if async_mode else "RequestResponse"

    logger.info(
        "Dispatching to %s (invocation_type=%s)", function_name, invocation_type
    )

    resp = client.invoke(
        FunctionName=function_name,
        InvocationType=invocation_type,
        Payload=json.dumps(payload).encode(),
    )

    if async_mode:
        return None

    raw = resp["Payload"].read()
    if not raw:
        return None
    return json.loads(raw)
