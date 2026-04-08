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
        team: Optional[str] = None,
    ) -> Dict[str, Any]:
        widgets = []
        if team:
            widgets.append({"textParagraph": {"text": f"🏷️ Team: {team}"}})
        if confirmation:
            widgets.append({"textParagraph": {"text": confirmation}})

        for meal_type, record in meals.items():
            display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
            is_in = record.is_participating if record is not None else True
            widgets.append({
                "decoratedText": {
                    "text": f"{display['emoji']} {display['label']}",
                    "bottomLabel": f"{'✅ Opted In' if is_in else '❌ Opted Out'}",
                }
            })

        widgets.append({"textParagraph": {
            "text": "<i>Use <b>/meal-update lunch</b> or <b>/meal-update snacks</b> to toggle</i>",
        }})

        return _wrap_card(
            card_id="meal_status",
            title="🍽️ Meal Participation",
            subtitle=format_date_display(target_date),
            sections=[{"widgets": widgets}],
        )

    # ── Location ─────────────────────────────────────────────────────────────

    def render_location_status(
        self,
        user_id: str,
        target_date: date,
        current: WorkLocationType,
        confirmation: Optional[str] = None,
        team: Optional[str] = None,
    ) -> Dict[str, Any]:
        widgets = []
        if team:
            widgets.append({"textParagraph": {"text": f"🏷️ Team: {team}"}})
        if confirmation:
            widgets.append({"textParagraph": {"text": confirmation}})

        display = LOCATION_DISPLAY.get(current, {"label": current.value, "emoji": "📍"})
        widgets.append({
            "decoratedText": {
                "text": f"{display['emoji']} Current Location",
                "bottomLabel": display["label"],
            }
        })

        widgets.append({"textParagraph": {
            "text": "<i>Use <b>/work-location office</b> or <b>/work-location wfh</b> to change</i>",
        }})

        return _wrap_card(
            card_id="location_status",
            title="📍 Work Location",
            subtitle=format_date_display(target_date),
            sections=[{"widgets": widgets}],
        )

    # ── Override ─────────────────────────────────────────────────────────────

    def render_override_status(
        self,
        target_user_id: str,
        target_username: str,
        actor_id: str,
        target_date: date,
        current_state: Dict[str, Any],
        confirmation: Optional[str] = None,
        target_team: Optional[str] = None,
    ) -> Dict[str, Any]:
        team_segment = target_team or ""

        widgets = []
        if confirmation:
            widgets.append({"textParagraph": {"text": confirmation}})

        widgets.append({
            "decoratedText": {
                "text": f"👤 Employee: {target_username}",
                "bottomLabel": f"📅 {format_date_display(target_date)}",
            }
        })

        for meal_type in DEFAULT_MEAL_TYPES:
            display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
            is_in = current_state["meals"].get(meal_type, True)
            widgets.append({
                "decoratedText": {
                    "text": f"{display['emoji']} {display['label']}",
                    "bottomLabel": f"{'✅ Opted In' if is_in else '❌ Opted Out'}",
                }
            })

        loc = current_state["location"]
        loc_display = LOCATION_DISPLAY.get(loc, {"label": loc.value, "emoji": "📍"})
        widgets.append({
            "decoratedText": {
                "text": f"{loc_display['emoji']} Work Location",
                "bottomLabel": loc_display["label"],
            }
        })

        # Text-based override instructions (replaces interactive buttons)
        date_iso = target_date.isoformat()
        meal_lines = []
        for meal_type in DEFAULT_MEAL_TYPES:
            display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
            is_in = current_state["meals"].get(meal_type, True)
            status = "✅ In" if is_in else "❌ Out"
            meal_lines.append(
                f"{display['emoji']} {display['label']} ({status}): "
                f"<b>/override-update employee:{target_user_id} date:{date_iso} meal:{meal_type.value}</b>"
            )

        loc_lines = []
        for loc_type in (WorkLocationType.OFFICE, WorkLocationType.WFH):
            ld = LOCATION_DISPLAY.get(loc_type, {"label": loc_type.value, "emoji": "📍"})
            if loc_type != loc:
                loc_lines.append(
                    f"{ld['emoji']} Switch to {ld['label']}: "
                    f"<b>/override-update employee:{target_user_id} date:{date_iso} location:{loc_type.value}</b>"
                )

        instruction_text = "<i>To toggle a meal or change location, use one of these commands:</i>\n\n"
        instruction_text += "\n".join(meal_lines)
        if loc_lines:
            instruction_text += "\n" + "\n".join(loc_lines)

        widgets.append({"textParagraph": {"text": instruction_text}})

        return _wrap_card(
            card_id="override_status",
            title="🔧 Override Update",
            subtitle="Overrides are recorded for audit purposes",
            sections=[{"widgets": widgets}],
        )

    # ── Headcount / Summary ───────────────────────────────────────────────────

    def render_team_summary(
        self,
        target_date: date,
        team_name: str,
        summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        sections = [{"widgets": _build_summary_widgets(summary)}]

        members = summary.get("members", [])
        if members:
            member_widgets = []
            for member in members:
                name = member.get("display_name") or member.get("user_id", "Unknown")
                meal_parts = []
                for meal_type, is_in in member.get("meals", {}).items():
                    display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
                    meal_parts.append(f"{display['emoji']}{'✅' if is_in else '❌'}")
                loc_val = member.get("location")
                if loc_val:
                    loc_display = LOCATION_DISPLAY.get(loc_val, {"emoji": "📍", "label": str(loc_val)})
                    loc_part = f"{loc_display['emoji']} {loc_display['label']}"
                else:
                    loc_part = "❓ No response"
                bottom = ((" ".join(meal_parts) + "  ") if meal_parts else "") + loc_part
                member_widgets.append({
                    "decoratedText": {
                        "text": name,
                        "bottomLabel": bottom,
                    }
                })
            sections.append({"header": "👤 Member Details", "widgets": member_widgets})

        return _wrap_card(
            card_id="team_summary",
            title=f"📊 Team Summary — {team_name}",
            subtitle=format_date_display(target_date),
            sections=sections,
        )

    def render_headcount_summary(
        self,
        target_date: date,
        summary: Dict[str, Any],
        team_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        title = f"📊 Headcount Summary{f' — {team_filter}' if team_filter else ''}"
        sections = [{"widgets": _build_summary_widgets(summary)}]

        for team, tdata in summary.get("team_breakdown", {}).items():
            sections.append({
                "header": team,
                "widgets": _build_summary_widgets(tdata),
            })

        return _wrap_card(
            card_id="headcount_summary",
            title=title,
            subtitle=format_date_display(target_date),
            sections=sections,
        )

    # ── Utilities ─────────────────────────────────────────────────────────────

    def render_success(self, message: str) -> Dict[str, Any]:
        return _render_text(f"✅ {message}")

    def render_error(self, message: str) -> Dict[str, Any]:
        return _render_text(f"❌ {message}")

    def render_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Return the card update format Google Chat HTTP apps require for CARD_CLICKED responses."""
        try:
            cards_v2 = (
                payload["renderActions"]["hostAppAction"]["chatAction"]
                ["createMessageAction"]["message"]["cardsV2"]
            )
            return {
                "actionResponse": {"type": "UPDATE_MESSAGE"},
                "cardsV2": cards_v2,
            }
        except (KeyError, TypeError):
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


def _build_summary_widgets(summary: Dict[str, Any]) -> list:
    widgets = []

    special_day = summary.get("special_day")
    if special_day:
        note = f" — {special_day.note}" if special_day.note else ""
        widgets.append({"textParagraph": {"text": f"⚠️ {special_day.day_type.value}{note}"}})

    total = summary.get("total_responding", 0)
    widgets.append({"textParagraph": {"text": f"👥 <b>{total}</b> employee(s) responded"}})

    for meal_type, counts in summary.get("meal_counts", {}).items():
        display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
        opted_in = counts["opted_in"]
        opted_out = counts["opted_out"]
        widgets.append({
            "decoratedText": {
                "text": f"{display['emoji']} {display['label']}",
                "bottomLabel": f"✅ {opted_in} opted in  •  ❌ {opted_out} opted out",
            }
        })

    loc = summary.get("location_count", {})
    widgets.append({
        "decoratedText": {
            "text": "📍 Work Location",
            "bottomLabel": f"🏢 {loc.get('office', 0)} Office  •  🏠 {loc.get('wfh', 0)} WFH",
        }
    })

    return widgets
