from datetime import date
from typing import Any, Dict, Optional

from src.adapters.base import UIRenderer
from src.models import MealType, WorkLocationType, MealParticipation
from src.services.meal_service import MEAL_DISPLAY, DEFAULT_MEAL_TYPES
from src.services.location_service import LOCATION_DISPLAY
from src.utils import format_date_display


class GoogleChatRenderer(UIRenderer):

    # ── Meal ─────────────────────────────────────────────────────────────────

    def render_meal_status(
        self,
        user_id: str,
        target_date: date,
        meals: Dict[MealType, Optional[MealParticipation]],
        confirmation: Optional[str] = None,
    ) -> Dict[str, Any]:
        lines = [f"🍽️ *Meal Participation — {format_date_display(target_date)}*"]
        if confirmation:
            lines.append(confirmation)
        for meal_type, record in meals.items():
            display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
            is_in = record.is_participating if record is not None else True
            lines.append(f"{display['emoji']} {display['label']}: {'✅ Opted In' if is_in else '❌ Opted Out'}")
        return _render_text("\n".join(lines))

    # ── Location ─────────────────────────────────────────────────────────────

    def render_location_status(
        self,
        user_id: str,
        target_date: date,
        current: WorkLocationType,
        confirmation: Optional[str] = None,
    ) -> Dict[str, Any]:
        widgets = []
        if confirmation:
            widgets.append({"textParagraph": {"text": confirmation}})

        display = LOCATION_DISPLAY.get(current, {"label": current.value, "emoji": "📍"})
        widgets.append({
            "decoratedText": {
                "text": f"{display['emoji']} Current Location",
                "bottomLabel": display["label"],
            }
        })

        buttons = []
        for loc_type in (WorkLocationType.OFFICE, WorkLocationType.WFH):
            loc_display = LOCATION_DISPLAY.get(loc_type, {"label": loc_type.value, "emoji": "📍"})
            is_active = loc_type == current
            action_id = f"location_set:{user_id}:{target_date.isoformat()}:{loc_type.value}"
            buttons.append({
                "text": f"{loc_display['emoji']} {loc_display['label']} {'✅' if is_active else ''}",
                "color": _green() if is_active else _grey(),
                "disabled": is_active,
                "onClick": {
                    "action": {
                        "function": "location_set",
                        "parameters": [{"key": "action_id", "value": action_id}],
                    }
                },
            })

        return _wrap_card(
            card_id="location_status",
            title="📍 Work Location",
            subtitle=format_date_display(target_date),
            sections=[
                {"widgets": widgets},
                {"widgets": [{"buttonList": {"buttons": buttons}}]},
            ],
        )

    

    # ── Utilities ─────────────────────────────────────────────────────────────

    def render_success(self, message: str) -> Dict[str, Any]:
        return _render_text(f"✅ {message}")

    def render_error(self, message: str) -> Dict[str, Any]:
        return _render_text(f"❌ {message}")

    def render_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Wrap card payload as an in-place message update."""
        return payload


# ── Private helpers ───────────────────────────────────────────────────────────

def _wrap_card(
    card_id: str,
    title: str,
    subtitle: str,
    sections: list,
) -> Dict[str, Any]:
    return {
        "renderActions": {
            "hostAppAction": {
                "chatAction": {
                    "createMessageAction": {
                        "message": {
                            "cardsV2": [{
                                "cardId": card_id,
                                "card": {
                                    "header": {"title": title, "subtitle": subtitle},
                                    "sections": sections,
                                },
                            }]
                        }
                    }
                }
            }
        }
    }


def _render_text(text: str) -> Dict[str, Any]:
    return {
        "renderActions": {
            "hostAppAction": {
                "chatAction": {
                    "createMessageAction": {
                        "message": {"text": text}
                    }
                }
            }
        }
    }


def _green() -> Dict[str, Any]:
    return {"red": 0.341, "green": 0.694, "blue": 0.278, "alpha": 1}


def _red() -> Dict[str, Any]:
    return {"red": 0.929, "green": 0.259, "blue": 0.271, "alpha": 1}


def _grey() -> Dict[str, Any]:
    return {"red": 0.6, "green": 0.6, "blue": 0.6, "alpha": 1}
