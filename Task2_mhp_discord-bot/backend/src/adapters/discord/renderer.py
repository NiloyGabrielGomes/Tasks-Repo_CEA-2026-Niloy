from datetime import date
from typing import Any, Dict, Optional

from src.adapters.base import UIRenderer
from src.models import MealType, WorkLocationType, MealParticipation
from src.services.meal_service import MEAL_DISPLAY
from src.services.location_service import LOCATION_DISPLAY
from src.services.meal_service import DEFAULT_MEAL_TYPES
from src.utils import format_date_display

# Discord response types
RESPONSE_CHANNEL_MESSAGE = 4
RESPONSE_UPDATE_MESSAGE = 7
EPHEMERAL_FLAG = 64

# Discord component types
ACTION_ROW = 1
BUTTON = 2

# Discord button styles
BUTTON_PRIMARY = 1    # Blurple
BUTTON_SECONDARY = 2  # Grey
BUTTON_SUCCESS = 3    # Green
BUTTON_DANGER = 4     # Red

OVERRIDE_EMBED_COLOR = 0xED4245  # Red — distinct from self-service





def _build_override_buttons(
    actor_id: str,
    target_user_id: str,
    target_date: date,
    current_state: dict,
    target_team: str | None = None,
) -> list[Dict[str, Any]]:

    team_segment = target_team or ""

    meal_buttons: list[Dict[str, Any]] = []
    for meal_type in DEFAULT_MEAL_TYPES:
        display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
        is_in = current_state["meals"].get(meal_type, True)
        new_state = "out" if is_in else "in"
        custom_id = (
            f"override_meal:{actor_id}:{target_user_id}:{target_date.isoformat()}"
            f":{meal_type.value}:{new_state}:{team_segment}"
        )
        style = BUTTON_SUCCESS if is_in else BUTTON_DANGER
        label = f"{display['emoji']} {display['label']} {'✅' if is_in else '❌'}"
        meal_buttons.append({"type": BUTTON, "style": style, "label": label, "custom_id": custom_id})

    loc_buttons: list[Dict[str, Any]] = []
    current_loc = current_state["location"]
    for loc_type in (WorkLocationType.OFFICE, WorkLocationType.WFH):
        loc_display = LOCATION_DISPLAY.get(loc_type, {"label": loc_type.value, "emoji": "📍"})
        is_active = loc_type == current_loc
        custom_id = (
            f"override_loc:{actor_id}:{target_user_id}:{target_date.isoformat()}"
            f":{loc_type.value}:{team_segment}"
        )
        style = BUTTON_SUCCESS if is_active else BUTTON_SECONDARY
        label = f"{loc_display['emoji']} {loc_display['label']} {'✅' if is_active else ''}"
        loc_buttons.append({
            "type": BUTTON, "style": style, "label": label,
            "custom_id": custom_id, "disabled": is_active,
        })

    return [
        {"type": ACTION_ROW, "components": meal_buttons},
        {"type": ACTION_ROW, "components": loc_buttons},
    ]
