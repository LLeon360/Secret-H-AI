# responders/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from core.game_state import GameState
from observers.base import GameStateObserver

class InputType(Enum):
    CHANCELLOR_NOMINATION = "chancellor_nomination"
    VOTE = "vote"
    POLICY_SELECTION = "policy_selection"
    DISCUSSION = "discussion"
    POWER_ACTION = "power_action"
    CONFIRMATION = "confirmation"

@dataclass
class InputField:
    """Represents a single input field"""
    name: str
    field_type: str  # "choice", "text", "boolean"
    prompt: str
    options: Optional[List[Any]] = None
    required: bool = True
    default: Optional[Any] = None

@dataclass 
class ExampleResponse:
    """Example response to guide responders"""
    values: Dict[str, Any]

@dataclass
class InputRequest:
    """Complete input request with all necessary information"""
    input_type: InputType
    player_id: str
    context: GameState
    fields: List[InputField]
    example: ExampleResponse

class Responder(ABC):
    def __init__(self, player_id: str):
        self.player_id = player_id
        
    @property
    def observer(self) -> Optional[GameStateObserver]:
        """Optional observer binding"""
        return None
        
    @abstractmethod
    def get_response(self, request: InputRequest) -> Dict[str, Any]:
        pass