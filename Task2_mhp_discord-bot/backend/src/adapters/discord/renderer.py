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


class DiscordRenderer(UIRenderer):
    """Produces Discord-flavoured JSON responses (embeds + action rows)."""

    # ── Meal ─────────────────────────────────────────────────────────────────

    def render_meal_status(
        self,
        user_id: str,
        target_date: date,
        meals: Dict[MealType, Optional[MealParticipation]],
        confirmation: Optional[str] = None,
        team: Optional[str] = None,
    ) -> Dict[str, Any]:
        embed = _build_meal_embed(user_id, target_date, meals, confirmation, team=team)
        components = _build_meal_buttons(user_id, target_date, meals)
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {
                "embeds": [embed],
                "components": components,
                "flags": EPHEMERAL_FLAG,
            },
        }

    # ── Location ─────────────────────────────────────────────────────────────

    def render_location_status(
        self,
        user_id: str,
        target_date: date,
        current: WorkLocationType,
        confirmation: Optional[str] = None,
        team: Optional[str] = None,
    ) -> Dict[str, Any]:
        embed = _build_location_embed(user_id, target_date, current, confirmation, team=team)
        components = _build_location_buttons(user_id, target_date, current)
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {
                "embeds": [embed],
                "components": components,
                "flags": EPHEMERAL_FLAG,
            },
        }

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
        embed = _build_override_embed(
            target_user_id, target_username, target_date, current_state, confirmation
        )
        components = _build_override_buttons(actor_id, target_user_id, target_date, current_state, target_team)
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {
                "embeds": [embed],
                "components": components,
                "flags": EPHEMERAL_FLAG,
            },
        }

    # ── Headcount / Summary ───────────────────────────────────────────────────

    def render_team_summary(
        self,
        target_date: date,
        team_name: str,
        summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        embed = _build_team_summary_embed(target_date, team_name, summary)
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {"embeds": [embed], "flags": EPHEMERAL_FLAG},
        }

    def render_headcount_summary(
        self,
        target_date: date,
        summary: Dict[str, Any],
        team_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        embed = _build_headcount_summary_embed(target_date, summary, team_filter)
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {"embeds": [embed], "flags": EPHEMERAL_FLAG},
        }

    # ── Utilities ─────────────────────────────────────────────────────────────

    def render_success(self, message: str) -> Dict[str, Any]:
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {"content": f"✅ {message}", "flags": EPHEMERAL_FLAG},
        }

    def render_error(self, message: str) -> Dict[str, Any]:
        return {
            "type": RESPONSE_CHANNEL_MESSAGE,
            "data": {"content": f"❌ {message}", "flags": EPHEMERAL_FLAG},
        }

    def render_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a new-message payload (type 4) to an in-place update (type 7)."""
        data = dict(payload.get("data", {}))
        data.pop("flags", None)  # ephemeral flag is not valid on UPDATE_MESSAGE
        return {"type": RESPONSE_UPDATE_MESSAGE, "data": data}


# ── Private builders ─────────────────────────────────────────────────────────

def _build_meal_embed(
    user_id: str,
    target_date: date,
    meals: Dict[MealType, Optional[MealParticipation]],
    confirmation: Optional[str] = None,
    team: Optional[str] = None,
) -> Dict[str, Any]:
    fields = []
    for meal_type, record in meals.items():
        display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
        is_in = record.is_participating if record is not None else True
        status_emoji = "✅" if is_in else "❌"
        status_text = "Opted In" if is_in else "Opted Out"
        fields.append({
            "name": f"{display['emoji']} {display['label']}",
            "value": f"{status_emoji} {status_text}",
            "inline": True,
        })

    date_line = f"📅 **{format_date_display(target_date)}**"
    if confirmation:
        description = f"{date_line}\n\n{confirmation}\n\nClick a button below to toggle your participation for each meal."
    else:
        description = f"{date_line}\n\nClick a button below to toggle your participation for each meal."

    footer_text = "Default: Opted In for all meals • Toggle to change"
    if team:
        footer_text = f"🏷️ Team: {team}  •  {footer_text}"

    return {
        "title": "🍽️ Meal Participation",
        "description": description,
        "fields": fields,
        "color": 0x5865F2,  # Discord blurple
        "footer": {"text": footer_text},
    }


def _build_meal_buttons(
    user_id: str,
    target_date: date,
    meals: Dict[MealType, Optional[MealParticipation]],
) -> list[Dict[str, Any]]:
    buttons = []
    for meal_type, record in meals.items():
        display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
        is_in = record.is_participating if record is not None else True
        custom_id = f"meal_toggle:{user_id}:{target_date.isoformat()}:{meal_type.value}"
        style = BUTTON_SUCCESS if is_in else BUTTON_DANGER
        label = f"{display['emoji']} {display['label']} {'✅' if is_in else '❌'}"
        buttons.append({"type": BUTTON, "style": style, "label": label, "custom_id": custom_id})

    rows = []
    for i in range(0, len(buttons), 5):
        rows.append({"type": ACTION_ROW, "components": buttons[i:i + 5]})
    return rows


def _build_location_embed(
    user_id: str,
    target_date: date,
    current: WorkLocationType,
    confirmation: Optional[str] = None,
    team: Optional[str] = None,
) -> Dict[str, Any]:
    display = LOCATION_DISPLAY.get(current, {"label": current.value, "emoji": "📍"})
    status_line = f"{display['emoji']} **{display['label']}**"

    parts = [f"📅 **{format_date_display(target_date)}**", ""]
    if confirmation:
        parts += [confirmation, ""]
    parts += [f"Current location: {status_line}", "", "Click a button below to change your work location."]

    footer_text = "Default: Office • WFH days count toward monthly cap"
    if team:
        footer_text = f"🏷️ Team: {team}  •  {footer_text}"

    return {
        "title": "📍 Work Location",
        "description": "\n".join(parts),
        "color": 0x57F287 if current == WorkLocationType.OFFICE else 0xFEE75C,
        "footer": {"text": footer_text},
    }


def _build_location_buttons(
    user_id: str,
    target_date: date,
    current: WorkLocationType,
) -> list[Dict[str, Any]]:
    buttons = []
    for loc_type in (WorkLocationType.OFFICE, WorkLocationType.WFH):
        display = LOCATION_DISPLAY.get(loc_type, {"label": loc_type.value, "emoji": "📍"})
        custom_id = f"location_set:{user_id}:{target_date.isoformat()}:{loc_type.value}"
        is_active = loc_type == current
        style = BUTTON_SUCCESS if is_active else BUTTON_SECONDARY
        label = f"{display['emoji']} {display['label']} {'✅' if is_active else ''}"
        buttons.append({
            "type": BUTTON, "style": style, "label": label,
            "custom_id": custom_id, "disabled": is_active,
        })
    return [{"type": ACTION_ROW, "components": buttons}]


def _build_override_embed(
    target_user_id: str,
    target_username: str,
    target_date: date,
    current_state: dict,
    confirmation: Optional[str] = None,
) -> Dict[str, Any]:
    fields = []
    for meal_type in DEFAULT_MEAL_TYPES:
        display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
        is_in = current_state["meals"].get(meal_type, True)
        status_emoji = "✅" if is_in else "❌"
        fields.append({
            "name": f"{display['emoji']} {display['label']}",
            "value": f"{status_emoji} {'Opted In' if is_in else 'Opted Out'}",
            "inline": True,
        })

    loc = current_state["location"]
    loc_display = LOCATION_DISPLAY.get(loc, {"label": loc.value, "emoji": "📍"})
    fields.append({
        "name": f"{loc_display['emoji']} Work Location",
        "value": f"**{loc_display['label']}**",
        "inline": True,
    })

    parts = [
        f"👤 **Employee:** <@{target_user_id}> ({target_username})",
        f"📅 **Date:** {format_date_display(target_date)}",
    ]
    if confirmation:
        parts += ["", confirmation]
    parts += ["", "Use the buttons below to update this employee's records."]

    return {
        "title": "🔧 Override Update",
        "description": "\n".join(parts),
        "fields": fields,
        "color": OVERRIDE_EMBED_COLOR,
        "footer": {"text": "Overrides are recorded for audit purposes"},
    }


def _build_team_summary_embed(
    target_date: date,
    team_name: str,
    summary: Dict[str, Any],
) -> Dict[str, Any]:
    special_day = summary.get("special_day")
    total = summary.get("total_responding", 0)

    parts = [f"📅 **{format_date_display(target_date)}**"]
    if special_day:
        parts.append(f"⚠️ *{special_day.day_type.value}*{f' — {special_day.note}' if special_day.note else ''}")
    parts.append(f"👥 **{total}** employee(s) have submitted data")

    fields = []
    for meal_type, counts in summary.get("meal_counts", {}).items():
        display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
        opted_in = counts["opted_in"]
        opted_out = counts["opted_out"]
        fields.append({
            "name": f"{display['emoji']} {display['label']}",
            "value": f"✅ {opted_in} opted in  •  ❌ {opted_out} opted out",
            "inline": True,
        })

    loc = summary.get("location_count", {})
    fields.append({
        "name": "📍 Work Location",
        "value": f"🏢 {loc.get('office', 0)} Office  •  🏠 {loc.get('wfh', 0)} WFH",
        "inline": True,
    })

    # Per-member breakdown
    members = summary.get("members", [])
    if members:
        fields.append({"name": "\u200b", "value": "**👤 Member Details**", "inline": False})
        for member in members[:25]:  # Discord embed field limit
            name = member.get("display_name") or member.get("user_id", "Unknown")
            meal_parts = []
            for meal_type, is_in in member.get("meals", {}).items():
                display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
                meal_parts.append(f"{display['emoji']}{'✅' if is_in else '❌'}")
            loc_val = member.get("location")
            if loc_val:
                loc_display = LOCATION_DISPLAY.get(loc_val, {"emoji": "📍"})
                loc_part = loc_display["emoji"]
            else:
                loc_part = "❓"
            meal_str = " ".join(meal_parts) if meal_parts else "*(no meals)*"
            fields.append({
                "name": name,
                "value": f"{meal_str}  {loc_part}",
                "inline": True,
            })
        if len(members) > 25:
            fields.append({
                "name": "\u200b",
                "value": f"*…and {len(members) - 25} more member(s)*",
                "inline": False,
            })

    return {
        "title": f"📊 Team Summary — {team_name}",
        "description": "\n".join(parts),
        "fields": fields,
        "color": 0x5865F2,
        "footer": {"text": "Showing all team members • ❓ = no response yet"},
    }


def _build_headcount_summary_embed(
    target_date: date,
    summary: Dict[str, Any],
    team_filter: Optional[str] = None,
) -> Dict[str, Any]:
    special_day = summary.get("special_day")
    total = summary.get("total_responding", 0)
    title = f"📊 Headcount Summary{f' — {team_filter}' if team_filter else ''}"

    parts = [f"📅 **{format_date_display(target_date)}**"]
    if special_day:
        parts.append(f"⚠️ *{special_day.day_type.value}*{f' — {special_day.note}' if special_day.note else ''}")
    parts.append(f"👥 **{total}** employee(s) total")

    fields = []
    for meal_type, counts in summary.get("meal_counts", {}).items():
        display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
        fields.append({
            "name": f"{display['emoji']} {display['label']}",
            "value": f"✅ {counts['opted_in']} opted in  •  ❌ {counts['opted_out']} opted out",
            "inline": True,
        })

    loc = summary.get("location_count", {})
    fields.append({
        "name": "📍 Work Location",
        "value": f"🏢 {loc.get('office', 0)} Office  •  🏠 {loc.get('wfh', 0)} WFH",
        "inline": True,
    })

    # Per-team breakdown (admin all-teams view)
    team_breakdown = summary.get("team_breakdown", {})
    if team_breakdown:
        fields.append({"name": "\u200b", "value": "**Team Breakdown**", "inline": False})
        for team, tdata in team_breakdown.items():
            meal_lines = []
            for meal_type, counts in tdata.get("meal_counts", {}).items():
                display = MEAL_DISPLAY.get(meal_type, {"label": meal_type.value, "emoji": "🍽️"})
                meal_lines.append(f"{display['emoji']} ✅{counts['opted_in']}/❌{counts['opted_out']}")
            tloc = tdata.get("location_count", {})
            loc_line = f"🏢{tloc.get('office', 0)} 🏠{tloc.get('wfh', 0)}"
            fields.append({
                "name": f"🏷️ {team} ({tdata.get('total_responding', 0)})",
                "value": "  ".join(meal_lines) + f"  {loc_line}",
                "inline": False,
            })

    return {
        "title": title,
        "description": "\n".join(parts),
        "fields": fields,
        "color": 0x5865F2,
        "footer": {"text": "Showing employees who have submitted data for this date"},
    }


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
