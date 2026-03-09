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