# Handles /meal-update slash command and meal toggle button interactions
import logging
from datetime import date
from typing import Any, Dict

from src.handlers.auth import AuthenticatedUser
from src.models import MealType
from src.services.meal_service import meal_service, MEAL_DISPLAY
from src.utils import parse_date_option, format_date_display, validate_date_for_update

logger = logging.getLogger(__name__)

# Discord response types
RESPONSE_CHANNEL_MESSAGE = 4
RESPONSE_UPDATE_MESSAGE = 7

# Discord component types
ACTION_ROW = 1
BUTTON = 2

# Discord button styles
BUTTON_PRIMARY = 1    # Blurple (opted in)
BUTTON_SECONDARY = 2  # Grey
BUTTON_SUCCESS = 3    # Green (opted in)
BUTTON_DANGER = 4     # Red (opted out)

# Custom ID prefix for meal toggle buttons
MEAL_TOGGLE_PREFIX = "meal_toggle"


