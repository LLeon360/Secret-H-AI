from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import json

class InputType(Enum):
    CHANCELLOR_NOMINATION = "chancellor_nomination"
    VOTE = "vote"
    POLICY_SELECTION = "policy_selection"
    DISCUSSION = "discussion"
    POWER_ACTION = "power_action"
    CONFIRMATION = "confirmation"

@dataclass
class ResponseFormat:
    """Specifies the expected format of the response"""
    schema: Dict[str, Any]  # JSON schema of expected response
    example: Dict[str, Any]  # Example response
    required_fields: List[str]  # Fields that must be present

@dataclass
class InputRequest:
    input_type: InputType
    player_id: str
    context: str  # Formatted string containing all relevant game info
    prompt: str   # What we're asking for
    response_format: ResponseFormat
    options: List[Any]  # Available choices if applicable

class Responder(ABC):
    @abstractmethod
    def get_response(self, request: InputRequest) -> Dict[str, Any]:
        """Get response given context and prompt"""
        pass

class HumanResponder(Responder):
    def get_response(self, request: InputRequest) -> Dict[str, Any]:
        """Break down the response format into individual prompts for human input"""
        print("\n=== Input Request ===")
        print("\nContext:")
        print(request.context)
        print("\nPrompt:", request.prompt)
        
        response = {}
        
        for field in request.response_format.required_fields:
            if field == "choice" and request.options:
                print("\nOptions:")
                for i, option in enumerate(request.options, 1):
                    print(f"{i}. {option}")
                while True:
                    try:
                        choice = int(input("\nEnter your choice (number): ")) - 1
                        if 0 <= choice < len(request.options):
                            response["choice"] = choice
                            break
                        print("Invalid choice, try again.")
                    except ValueError:
                        print("Please enter a number.")
                        
            elif field == "confirmation":
                while True:
                    value = input(f"\nEnter {field} (y/n): ").lower()
                    if value in ['y', 'n']:
                        response[field] = value == 'y'
                        break
                    print("Invalid input. Please enter 'y' or 'n'.")
                    
            elif field == "justification" or field == "message":
                response[field] = input(f"\nEnter {field}: ")
                
        return response

class ModelResponder(Responder):
    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt

    def get_response(self, request: InputRequest) -> Dict[str, Any]:
        """Format request for model and parse response"""
        # This would be implemented with actual LLM integration
        # For now, just return a mock response
        raise NotImplementedError("Model responder not yet implemented")

class InputHandler:
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
