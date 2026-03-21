from datetime import date
from typing import Any, Dict, Optional

from src.adapters.base import UIRenderer
from src.models import MealType, WorkLocationType, MealParticipation
from src.services.meal_service import MEAL_DISPLAY, DEFAULT_MEAL_TYPES
from src.services.location_service import LOCATION_DISPLAY
from src.utils import format_date_display


class GoogleChatRenderer(UIRenderer):

   

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
