from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.handlers.auth import AuthenticatedUser
    from src.models import MealType, WorkLocationType, MealParticipation


class InteractionVerifier(ABC):
    """Authenticates incoming webhook requests from the platform."""

    @abstractmethod
    def verify(self, raw_event: Dict[str, Any]) -> bool:
        """Return True if the request is authentically from the platform."""

    @abstractmethod
    def extract_body(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Return the parsed JSON body (after verification)."""


class UserResolver(ABC):
    """Maps a platform-specific identity into an AuthenticatedUser."""

    @abstractmethod
    def resolve(self, raw_body: Dict[str, Any]) -> "AuthenticatedUser":
        """Extract platform identity, map roles, resolve team."""


class UIRenderer(ABC):
    """Produces platform-specific response payloads from business data."""

    # ── Meal ─────────────────────────────────────────────────────────────────

    @abstractmethod
    def render_meal_status(
        self,
        user_id: str,
        target_date: date,
        meals: Dict["MealType", Optional["MealParticipation"]],
        confirmation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return a response payload showing meal participation status."""

    # ── Location ─────────────────────────────────────────────────────────────

    @abstractmethod
    def render_location_status(
        self,
        user_id: str,
        target_date: date,
        current: "WorkLocationType",
        confirmation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return a response payload showing work location."""

