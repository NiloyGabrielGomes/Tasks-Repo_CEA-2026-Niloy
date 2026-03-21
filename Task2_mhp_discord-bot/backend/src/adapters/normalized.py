"""NormalizedInteraction — the bridge between platform ingress and business handlers."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.handlers.auth import AuthenticatedUser


@dataclass
class NormalizedInteraction:
    platform: str
    interaction_type: str           # "command" | "action"
    command_name: Optional[str]
    action_id: Optional[str]
    options: Dict[str, Any] = field(default_factory=dict)
    raw_body: Dict[str, Any] = field(default_factory=dict)
    user: Optional["AuthenticatedUser"] = None
