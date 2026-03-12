import logging
from datetime import date, datetime

from src.config import settings
from src.models import (
    MealParticipation, MealType, WorkLocation, WorkLocationType, UserRole,
)
from src.storage.dynamodb import DynamoDBStorage, storage as default_storage
from src.services.meal_service import meal_service as default_meal_service, MealService
from src.services.location_service import (
    location_service as default_location_service,
    LocationService,
)
from src.utils import validate_date_for_update, DHAKA_UTC_OFFSET

logger = logging.getLogger(__name__)


class OverrideService:
    def __init__(
        self,
        storage: DynamoDBStorage = None,
        meal_svc: MealService = None,
        location_svc: LocationService = None,
    ):
        self.storage = storage or default_storage
        self.meal_svc = meal_svc or default_meal_service
        self.location_svc = location_svc or default_location_service

    # ── Team-scope check ─────────────────────────────────────────────────────

    def check_team_scope(
        self,
        actor_role: UserRole,
        actor_team: str | None,
        target_team: str | None,
    ) -> tuple[bool, str | None]:
        if actor_role == UserRole.ADMIN:
            return True, None

        if actor_role == UserRole.TEAM_LEAD:
            if not actor_team:
                return False, (
                    "❌ Your team could not be determined from your Discord roles. "
                    "Please contact an admin."
                )
            if not target_team:
                return False, (
                    "❌ The target employee's team could not be determined. "
                    "Please contact an admin."
                )
            if actor_team != target_team:
                return False, (
                    f"❌ You can only override employees in your team "
                    f"(**{actor_team}**). The selected employee belongs to "
                    f"**{target_team}**."
                )
            return True, None

        # EMPLOYEE should never reach here (authorization gate catches it)
        return False, "❌ You don't have permission to use this command."
    
    # ── Override meal participation ───────────────────────────────────────────

    def override_meal(
        self,
        target_user_id: str,
        target_date: date,
        meal_type: MealType,
        is_participating: bool,
        actor_id: str,
        target_team: str | None = None,
    ) -> tuple[bool, MealParticipation | str]:
        # Validate date
        is_valid, error_msg = validate_date_for_update(target_date)
        if not is_valid:
            return False, error_msg

        now = datetime.now(DHAKA_UTC_OFFSET)

        meal = MealParticipation(
            user_id=target_user_id,
            meal_type=meal_type,
            date=target_date,
            is_participating=is_participating,
            team=target_team,
            updated_by=actor_id,  # audit: who overrode it
            updated_at=now,
        )

        self.storage.put_meal(meal)

        status_text = "opted in" if is_participating else "opted out"
        logger.info(
            "Override meal: actor=%s, target=%s, date=%s, meal=%s, status=%s",
            actor_id, target_user_id, target_date, meal_type.value, status_text,
        )

        return True, meal
    
    # ── Override work location ───────────────────────────────────────────────

    def override_location(
        self,
        target_user_id: str,
        target_date: date,
        location: WorkLocationType,
        actor_id: str,
        target_team: str | None = None,
    ) -> tuple[bool, WorkLocation | str]:
        # Validate date
        is_valid, error_msg = validate_date_for_update(target_date)
        if not is_valid:
            return False, error_msg

        # WFH cap check applies even for overrides
        if location == WorkLocationType.WFH:
            over_cap, cap_msg = self.location_svc._check_wfh_cap(
                target_user_id, target_date
            )
            if over_cap:
                return False, cap_msg

        now = datetime.now(DHAKA_UTC_OFFSET)

        record = WorkLocation(
            user_id=target_user_id,
            date=target_date,
            location=location,
            team=target_team,
            updated_by=actor_id,
            updated_at=now,
        )

        self.storage.put_location(record)

        logger.info(
            "Override location: actor=%s, target=%s, date=%s, location=%s",
            actor_id, target_user_id, target_date, location.value,
        )

        return True, record
    
    # ── Get current states for display ───────────────────────────────────────

    def get_target_current_state(
        self, target_user_id: str, target_date: date
    ) -> dict:
        meals = self.meal_svc.get_user_meals_for_date(target_user_id, target_date)
        location_record = self.location_svc.get_user_location_for_date(
            target_user_id, target_date
        )
        current_location = self.location_svc.get_current_location(location_record)

        meal_states = {}
        for meal_type, record in meals.items():
            is_in = self.meal_svc.get_participation_status(record)
            meal_states[meal_type] = is_in

        return {
            "meals": meal_states,
            "location": current_location,
        }
override_service = OverrideService()