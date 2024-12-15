# core/input_handler.py
from typing import Dict, Any
from responders.base import Responder, InputRequest

class InputHandler:
    """Handles routing input requests to appropriate responders"""
    
    def __init__(self):
        self.responders: Dict[str, Responder] = {}

    def register_responder(self, player_id: str, responder: Responder):
        """Register a responder for a player"""
        self.responders[player_id] = responder

    def get_input(self, request: InputRequest) -> Dict[str, Any]:
        """Get input using the appropriate responder"""
        responder = self.responders.get(request.player_id)
        if not responder:
            raise ValueError(f"No responder registered for player {request.player_id}")
        return responder.get_response(request)