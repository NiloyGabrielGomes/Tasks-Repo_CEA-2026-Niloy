# Business logic for headcount and team summary aggregation
import logging
from collections import defaultdict
from datetime import date
from typing import Any, Dict, List, Optional

from src.models import MealType, WorkLocationType
from src.services.meal_service import DEFAULT_MEAL_TYPES
from src.storage.dynamodb import DynamoDBStorage, storage as default_storage

logger = logging.getLogger(__name__)


class HeadcountService:

    def __init__(self, storage: DynamoDBStorage = None):
        self.storage = storage or default_storage

    def get_team_summary(self, target_date: date, team_name: str) -> Dict[str, Any]:
        """Aggregate meal + location data for a single team on a given date."""
        special_day = self.storage.get_special_day(target_date)
        meals = self.storage.get_meals_for_date_and_team(target_date, team_name)
        locations = self.storage.get_locations_for_date_and_team(target_date, team_name)

        user_ids = set(m.user_id for m in meals) | set(l.user_id for l in locations)

        return {
            "date": target_date,
            "team_name": team_name,
            "special_day": special_day,
            "meal_counts": _aggregate_meals(meals),
            "location_count": _aggregate_locations(locations),
            "total_responding": len(user_ids),
        }

    def get_headcount_summary(
        self, target_date: date, team_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Aggregate meal + location data across all (or one) team(s) on a given date."""
        special_day = self.storage.get_special_day(target_date)

        if team_filter:
            meals = self.storage.get_meals_for_date_and_team(target_date, team_filter)
            locations = self.storage.get_locations_for_date_and_team(target_date, team_filter)
        else:
            meals = self.storage.get_meals_for_date(target_date)
            locations = self.storage.get_locations_for_date(target_date)

        user_ids = set(m.user_id for m in meals) | set(l.user_id for l in locations)

        # Build per-team breakdown only when showing all teams
        team_breakdown: Dict[str, Any] = {}
        if not team_filter:
            team_meals: Dict[str, list] = defaultdict(list)
            team_locs: Dict[str, list] = defaultdict(list)

            for m in meals:
                if m.team:
                    team_meals[m.team].append(m)
            for loc in locations:
                if loc.team:
                    team_locs[loc.team].append(loc)

            for team in sorted(set(team_meals.keys()) | set(team_locs.keys())):
                t_user_ids = (
                    set(m.user_id for m in team_meals[team]) |
                    set(l.user_id for l in team_locs[team])
                )
                team_breakdown[team] = {
                    "meal_counts": _aggregate_meals(team_meals[team]),
                    "location_count": _aggregate_locations(team_locs[team]),
                    "total_responding": len(t_user_ids),
                }

        return {
            "date": target_date,
            "special_day": special_day,
            "meal_counts": _aggregate_meals(meals),
            "location_count": _aggregate_locations(locations),
            "total_responding": len(user_ids),
            "team_breakdown": team_breakdown,
            "team_filter": team_filter,
        }


# ── Private helpers ───────────────────────────────────────────────────────────

def _aggregate_meals(meals: List) -> Dict[MealType, Dict[str, int]]:
    counts: Dict[MealType, Dict[str, int]] = {
        mt: {"opted_in": 0, "opted_out": 0} for mt in DEFAULT_MEAL_TYPES
    }
    for meal in meals:
        if meal.meal_type in counts:
            key = "opted_in" if meal.is_participating else "opted_out"
            counts[meal.meal_type][key] += 1
    return counts


def _aggregate_locations(locations: List) -> Dict[str, int]:
    result = {"office": 0, "wfh": 0}
    for loc in locations:
        if loc.location == WorkLocationType.OFFICE:
            result["office"] += 1
        elif loc.location == WorkLocationType.WFH:
            result["wfh"] += 1
    return result


headcount_service = HeadcountService()
