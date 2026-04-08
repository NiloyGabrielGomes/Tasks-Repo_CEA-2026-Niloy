# Business logic for work location CRUD + validation
import calendar
import logging
from datetime import date, datetime

from src.config import settings
from src.models import MealParticipation, WorkLocation, WorkLocationType
from src.storage.dynamodb import DynamoDBStorage, storage as default_storage
from src.utils import validate_date_for_update, DHAKA_UTC_OFFSET
from src.services.meal_service import DEFAULT_MEAL_TYPES

logger = logging.getLogger(__name__)

# Location display names and emoji
LOCATION_DISPLAY = {
    WorkLocationType.OFFICE: {"label": "Office", "emoji": "🏢"},
    WorkLocationType.WFH: {"label": "Work From Home", "emoji": "🏠"},
}


class LocationService:
    def __init__(self, storage: DynamoDBStorage = None):
        self.storage = storage or default_storage

    # ── Read ─────────────────────────────────────────────────────────────────

    def get_user_location_for_date(
        self, discord_id: str, target_date: date
    ) -> WorkLocation | None:
        return self.storage.get_location(discord_id, target_date)

    def get_current_location(self, record: WorkLocation | None) -> WorkLocationType:
        if record is None:
            return WorkLocationType.OFFICE
        return record.location

    # ── Write ────────────────────────────────────────────────────────────────

    def set_work_location(
        self,
        discord_id: str,
        target_date: date,
        location: WorkLocationType,
        updated_by: str | None = None,
        team: str | None = None,
    ) -> tuple[bool, WorkLocation | str]:
        # Validate date (same cutoff / past-date / forward-window rules as meals)
        is_valid, error_msg = validate_date_for_update(target_date)
        if not is_valid:
            return False, error_msg

        # Check WFH monthly cap when setting to WFH
        if location == WorkLocationType.WFH:
            over_cap, cap_msg = self._check_wfh_cap(discord_id, target_date)
            if over_cap:
                return False, cap_msg

        now = datetime.now(DHAKA_UTC_OFFSET)

        record = WorkLocation(
            user_id=discord_id,
            date=target_date,
            location=location,
            team=team,
            updated_by=updated_by or discord_id,
            updated_at=now,
        )

        self.storage.put_location(record)

        if location == WorkLocationType.WFH:
            for meal_type in DEFAULT_MEAL_TYPES:
                self.storage.put_meal(MealParticipation(
                    user_id=discord_id,
                    meal_type=meal_type,
                    date=target_date,
                    is_participating=False,
                    team=team,
                    updated_by=updated_by or discord_id,
                    updated_at=now,
                ))
            logger.info(
                "WFH set: auto opted-out of all meals for user=%s, date=%s",
                discord_id, target_date,
            )

        logger.info(
            "Location set: user=%s, date=%s, location=%s",
            discord_id, target_date, location.value,
        )

        return True, record

    # ── WFH Cap ──────────────────────────────────────────────────────────────

    def _check_wfh_cap(
        self, discord_id: str, target_date: date
    ) -> tuple[bool, str | None]:
        cap = settings.WFH_MONTHLY_CAP
        if cap <= 0:
            return False, None  # disabled

        first_of_month = target_date.replace(day=1)
        locations = self.storage.get_locations_for_date_range(
            discord_id, first_of_month, target_date
        ) if hasattr(self.storage, "get_locations_for_date_range") else []

        # Fallback: count from all locations we can access
        if not locations:
            locations = self._get_user_wfh_days_in_month(discord_id, target_date)

        wfh_count = sum(
            1 for loc in locations
            if loc.location == WorkLocationType.WFH
            and loc.date.month == target_date.month
            and loc.date.year == target_date.year
            and loc.date != target_date  # don't count the date being set
        )

        if wfh_count >= cap:
            return True, (
                f"⚠️ You have already used {wfh_count}/{cap} WFH days this month "
                f"({target_date.strftime('%B %Y')}). Monthly soft limit reached."
            )

        return False, None

    def _get_user_wfh_days_in_month(
        self, discord_id: str, target_date: date
    ) -> list[WorkLocation]:

        year = target_date.year
        month = target_date.month
        _, last_day = calendar.monthrange(year, month)

        results: list[WorkLocation] = []
        for day_num in range(1, last_day + 1):
            d = date(year, month, day_num)
            loc = self.storage.get_location(discord_id, d)
            if loc is not None:
                results.append(loc)

        return results

    # ── Display helpers ──────────────────────────────────────────────────────

    def get_location_display_info(self, loc_type: WorkLocationType) -> dict:
        return LOCATION_DISPLAY.get(
            loc_type,
            {"label": loc_type.value.upper(), "emoji": "📍"},
        )
location_service = LocationService()
