# Centralized policy read/write with in-memory caching.
# Falls back to settings.* env var defaults when no DynamoDB policy exists.
import json
import logging
from datetime import datetime
from typing import Optional

from src.config import settings
from src.models import MealType, Policy

logger = logging.getLogger(__name__)

# Policy keys recognized by the system
POLICY_KEYS = ["cutoff_time", "wfh_monthly_cap", "forward_planning_days", "active_meal_types"]

# Display-friendly names for /policy view
POLICY_DISPLAY = {
    "cutoff_time": "Cutoff Time",
    "wfh_monthly_cap": "WFH Monthly Cap",
    "forward_planning_days": "Forward Planning Days",
    "active_meal_types": "Active Meal Types",
}

# Hardcoded fallback for active meal types (matches meal_service.DEFAULT_MEAL_TYPES)
_DEFAULT_MEAL_TYPES = [MealType.LUNCH, MealType.SNACKS]

# ── In-memory cache (per Lambda container) ──────────────────────────────────

_policy_cache: dict[str, Optional[str]] = {}


def _get_raw(policy_name: str) -> Optional[str]:
    """Read a policy value from cache or DynamoDB. Returns None if not set."""
    if policy_name not in _policy_cache:
        from src.storage.dynamodb import storage
        policy = storage.get_policy(policy_name)
        _policy_cache[policy_name] = policy.value if policy else None
    return _policy_cache[policy_name]


def invalidate_cache(name: Optional[str] = None) -> None:
    """Clear cached policy values. Pass name to clear one, or None to clear all."""
    if name:
        _policy_cache.pop(name, None)
    else:
        _policy_cache.clear()


# ── Typed accessors (DynamoDB → env var fallback) ────────────────────────────

def get_cutoff_time() -> str:
    return _get_raw("cutoff_time") or settings.CUTOFF_TIME


def get_wfh_monthly_cap() -> int:
    raw = _get_raw("wfh_monthly_cap")
    if raw is not None:
        try:
            return int(raw)
        except ValueError:
            logger.warning("Invalid wfh_monthly_cap policy value: %s", raw)
    return settings.WFH_MONTHLY_CAP


def get_forward_planning_days() -> int:
    raw = _get_raw("forward_planning_days")
    if raw is not None:
        try:
            return int(raw)
        except ValueError:
            logger.warning("Invalid forward_planning_days policy value: %s", raw)
    return settings.FORWARD_PLANNING_DAYS


def get_active_meal_types() -> list[MealType]:
    raw = _get_raw("active_meal_types")
    if raw:
        try:
            return [MealType(v) for v in json.loads(raw)]
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Invalid active_meal_types policy: %s", e)
    return list(_DEFAULT_MEAL_TYPES)


def get_all_policies() -> dict[str, str]:
    """Return all policy values (resolved with defaults) for /policy view."""
    return {
        "cutoff_time": get_cutoff_time(),
        "wfh_monthly_cap": str(get_wfh_monthly_cap()),
        "forward_planning_days": str(get_forward_planning_days()),
        "active_meal_types": ", ".join(m.value for m in get_active_meal_types()),
    }


# ── Write ────────────────────────────────────────────────────────────────────

def set_policy(name: str, value: str) -> None:
    """Write a policy to DynamoDB and invalidate the local cache."""
    from src.storage.dynamodb import storage
    storage.put_policy(Policy(name=name, value=value, updated_at=datetime.utcnow()))
    invalidate_cache(name)


# ── Validation helpers (for /policy set) ─────────────────────────────────────

def validate_policy_value(name: str, value: str) -> tuple[bool, Optional[str]]:
    """Validate a policy value before writing. Returns (ok, error_message)."""
    if name == "cutoff_time":
        parts = value.split(":")
        if len(parts) != 2:
            return False, "Cutoff time must be in HH:MM format."
        try:
            h, m = int(parts[0]), int(parts[1])
        except ValueError:
            return False, "Cutoff time must be in HH:MM format with numeric values."
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return False, "Hours must be 0-23 and minutes must be 0-59."
        return True, None

    if name == "wfh_monthly_cap":
        try:
            cap = int(value)
        except ValueError:
            return False, "WFH monthly cap must be a non-negative integer."
        if cap < 0:
            return False, "WFH monthly cap must be a non-negative integer."
        return True, None

    if name == "forward_planning_days":
        try:
            days = int(value)
        except ValueError:
            return False, "Forward planning days must be an integer between 1 and 30."
        if not (1 <= days <= 30):
            return False, "Forward planning days must be between 1 and 30."
        return True, None

    if name == "active_meal_types":
        types = [t.strip() for t in value.split(",") if t.strip()]
        if not types:
            return False, "At least one meal type is required."
        valid_values = [m.value for m in MealType]
        for t in types:
            if t not in valid_values:
                return False, f"Unknown meal type: `{t}`. Valid types: {', '.join(f'`{v}`' for v in valid_values)}."
        # Store as JSON array
        return True, None

    return False, f"Unknown policy: `{name}`. Valid policies: {', '.join(f'`{k}`' for k in POLICY_KEYS)}."
