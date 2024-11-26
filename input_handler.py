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
    values: Dict[str, Any]  # Example values showing expected format for each field

@dataclass
class InputRequest:
    """Complete input request with all necessary information"""
    input_type: InputType
    player_id: str
    context: str
    fields: List[InputField]  # Fields define both the structure and the prompts
    example: ExampleResponse  # Provides example of valid response values

class Responder(ABC):
    @abstractmethod
    def get_response(self, request: InputRequest) -> Dict[str, Any]:
        """Get response given context and prompt"""
        pass

class HumanResponder(Responder):
    def get_response(self, request: InputRequest) -> Dict[str, Any]:
        print("\n=== Input Request ===")
        print("\nContext:")
        print(request.context)
        
        response = {}
        
        for field in request.fields:
            print(f"\n{field.prompt}")
            
            if field.field_type == "choice" and field.options:
                print("\nOptions:")
                for i, option in enumerate(field.options, 1):
                    print(f"{i}. {option}")
                
                while True:
                    if not field.required:
                        print("(Press Enter to skip)")
                    try:
                        value = input("\nEnter your choice (number): ").strip()
                        if not field.required and not value:
                            response[field.name] = field.default
                            break
                        choice = int(value) - 1
                        if 0 <= choice < len(field.options):
                            response[field.name] = choice
                            break
                        print("Invalid choice, try again.")
                    except ValueError:
                        print("Please enter a number.")
                        
            elif field.field_type == "boolean":
                while True:
                    if not field.required:
                        print("(Press Enter to skip)")
                    value = input(f"\nEnter choice (y/n): ").lower().strip()
                    if not field.required and not value:
                        response[field.name] = field.default
                        break
                    if value in ['y', 'n']:
                        response[field.name] = value == 'y'
                        break
                    print("Invalid input. Please enter 'y' or 'n'.")
                    
            elif field.field_type == "text":
                while True:
                    if not field.required:
                        print("(Press Enter to skip)")
                    value = input(f"\nEnter your response: ").strip()
                    if not value:
                        if not field.required:
                            response[field.name] = field.default
                            break
                        elif field.required:
                            print("This field is required.")
                            continue
                    else:
                        response[field.name] = value
                        break
        
        return response

class ModelResponder(Responder):
    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt

    def get_response(self, request: InputRequest) -> Dict[str, Any]:
        """Format request for model and parse response"""
        prompt = f"""
        Context:
        {request.context}

        You need to make the following decision(s):
        """
        
        for field in request.fields:
            prompt += f"\n{field.prompt}"
            if field.options:
                prompt += f"\nOptions: {', '.join(str(opt) for opt in field.options)}"
                
        prompt += f"""
        
        Provide your response in the following JSON format:
        {json.dumps(request.response_format.example, indent=2)}
        """
        
        # This would be implemented with actual LLM integration
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