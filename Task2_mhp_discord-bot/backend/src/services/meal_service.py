# Business logic for meal participation CRUD + validation
import logging
from datetime import date, datetime

from src.config import settings
from src.models import MealParticipation, MealType
from src.storage.dynamodb import DynamoDBStorage, storage as default_storage
from src.utils import validate_date_for_update, DHAKA_UTC_OFFSET

logger = logging.getLogger(__name__)

# Default meal types available for daily participation
DEFAULT_MEAL_TYPES: list[MealType] = [
    MealType.LUNCH,
    MealType.SNACKS,
]

# Meal type display names and emoji
MEAL_DISPLAY = {
    MealType.LUNCH: {"label": "Lunch", "emoji": "🍱"},
    MealType.SNACKS: {"label": "Snacks", "emoji": "🍕"},
    MealType.IFTAR: {"label": "Iftar", "emoji": "🌙"},
    MealType.EVENT_DINNER: {"label": "Event Dinner", "emoji": "🎉"},
    MealType.OPTIONAL_DINNER: {"label": "Optional Dinner", "emoji": "🍽️"},
}


class MealService:

    def __init__(self, storage: DynamoDBStorage = None):
        self.storage = storage or default_storage

    def get_available_meal_types(self) -> list[MealType]:
        return list(DEFAULT_MEAL_TYPES)

    def get_user_meals_for_date(
        self, discord_id: str, target_date: date
    ) -> dict[MealType, MealParticipation | None]:
        meal_types = self.get_available_meal_types()
        result: dict[MealType, MealParticipation | None] = {}

        for meal_type in meal_types:
            record = self.storage.get_meal(discord_id, target_date, meal_type)
            result[meal_type] = record

        return result

    def toggle_meal_participation(
        self,
        discord_id: str,
        target_date: date,
        meal_type: MealType,
        updated_by: str | None = None,
    ) -> tuple[bool, MealParticipation | str]:
        # Validate date
        is_valid, error_msg = validate_date_for_update(target_date)
        if not is_valid:
            return False, error_msg

        # Get current status
        existing = self.storage.get_meal(discord_id, target_date, meal_type)

        if existing:
            # Toggle: flip is_participating
            new_status = not existing.is_participating
        else:
            # No record exists → default is opted-in → toggling means opt-out
            new_status = False

        now = datetime.now(DHAKA_UTC_OFFSET)

        meal = MealParticipation(
            user_id=discord_id,
            meal_type=meal_type,
            date=target_date,
            is_participating=new_status,
            updated_by=updated_by or discord_id,
            updated_at=now,
        )

        self.storage.put_meal(meal)

        status_text = "opted in" if new_status else "opted out"
        logger.info(
            f"Meal toggled: user={discord_id}, date={target_date}, "
            f"meal={meal_type.value}, status={status_text}"
        )

        return True, meal

    def get_participation_status(
        self, record: MealParticipation | None
    ) -> bool:
        if record is None:
            return True
        return record.is_participating

    def get_meal_display_info(self, meal_type: MealType) -> dict:
        return MEAL_DISPLAY.get(
            meal_type,
            {"label": meal_type.value.replace("_", " ").title(), "emoji": "🍽️"},
        )
meal_service = MealService()
