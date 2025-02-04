from abc import ABC, abstractmethod
from core.game_state import GameState, GameEvent

class GameStateObserver(ABC):
    """Base interface for game state observers"""
    
    def __init__(self, player_id: str):
        self.player_id = player_id
    
    @abstractmethod
    def on_state_change(self, state: GameState, event: GameEvent) -> None:
        """
        Handle game state updates
        Args:
            state: Current game state from observer's player perspective
            event: Event that triggered this update
        """
        pass