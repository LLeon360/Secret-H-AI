# Basilisk 

## Secret Hitler Game State Manager for Humans and LLMs 

A Python framework for simulating and tracking the state of Secret Hitler games, designed to support both human players and Language Learning Models (LLMs). The system provides a structured way to interact with the game state, making it easy to implement custom AI agents.

## Core Systems Overview

### 1. Game State Management
- Tracks complete game state (roles, policies, votes, etc.)
- Manages player actions and game flow
- Handles event logging and private information
- Enforces game rules and valid actions

### 2. Input/Response System
- Structured input requests with clear field specifications
- Consistent response format across all player types
- Validation of responses
- Support for different input types (choices, text, boolean)

### 3. Responder Interface
- Simple, single-method interface for implementing agents
- Complete game context provided with each request
- Clear response format requirements
- Support for memory and state tracking if desired

## Project Structure

```
basilisk/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── game_state.py      # Game state and rules
│   ├── game_manager.py    # Game flow and coordination
│   └── input_handler.py   # Input processing
├── responders/
│   ├── __init__.py
│   ├── base.py           # Responder interface
│   ├── human/
│   │   └── responder.py  # Human console interface
│   └── llm/
│       ├── __init__.py
│       ├── responder.py  # LLM responder
│       └── configs/
│           └── system.txt # System prompt
└── main.py               # Game setup and initialization
```

## Implementing a Custom Agent

The core interface for implementing an agent is the Responder class:

```python
from typing import Any, Dict
from responders.base import Responder, InputRequest

class CustomResponder(Responder):
    def get_response(self, request: InputRequest) -> Dict[str, Any]:
        """
        Process request and return response matching required format.
        
        Args:
            request: InputRequest containing:
                - input_type: Type of decision needed
                - context: Complete game state as an dataclass object
                - fields: Required response fields
                - example: Example response format
        
        Returns:
            Dictionary matching the format specified in request.fields
        """
        pass
```

For details, see `basilisk/responders/llm/responder.py` or `basilisk/responders/llm/human.py` for reference.

### Input Request Format

Each request contains:

```python
@dataclass
class InputRequest:
    input_type: InputType  # e.g., VOTE, POLICY_SELECTION
    player_id: str        # ID of player making decision
    context: GameState    # game state dataclass which may be formatted to natural language with GameStateTextFormatter 
    fields: List[InputField]  # Required response fields
    example: ExampleResponse  # Example of valid response
```

Example request for policy selection:
```python
    fields = [
        InputField(
            name="policy",
            field_type="choice",
            prompt=f"Choose a policy to {action_type}:",
            options=[f"Policy: {policy.value}" for policy in policies],
            required=True
        ),
        InputField(
            name="claimed_policy",
            field_type="choice",
            prompt="What policy will you claim to have discarded?",
            options=["liberal", "fascist", "undisclosed"],
            required=False,
            default=2  # Default to undisclosed
        ),
        InputField(
            name="justification",
            field_type="text",
            prompt="Explain your choice:",
            required=True
        )
    ]

    request = InputRequest(
        input_type=InputType.POLICY_SELECTION,
        player_id=player_id,
        context=self.format_context(player_id),
        fields=fields,
        example=ExampleResponse(
            values={
                "policy": 0,
                "claimed_policy": 2,
                "justification": "This advances our team's goals"
            }
        )
    )
```

### Game State Context

The formatted context provided in each request looks like:

```
Context:

==================== Game Status ====================

Turn 0
You are Unsuspecting Human
Your Role: Liberal
Current Phase: President Discard

Policies Enacted:
Liberal Track: ⚪⚪⚪⚪⚪ (0/5)
Fascist Track: ⚪⚪⚪⚪⚪⚪ (0/6)

Current Government:
President: Unsuspecting Human
Chancellor: Bot_1

Last Government: Unsuspecting Human (P), Bot_1 (C)

Players:
  • Unsuspecting Human (President)
  • Bot_1 (Chancellor)
  • Bot_2
  • Bot_3
  • Bot_4

==================== Recent Events ====================

[Turn 0] Game started with 5 players
Reasoning: "Game initialized"

[Turn 0] Unsuspecting Human nominated Bot_1 as Chancellor
Reasoning: "no"

[Turn 0] Unsuspecting Human voted Nein!
Reasoning: "no"

[Turn 0] Bot_1 voted Ja!
Reasoning: "I am new to the game, and I believe that Bot_1 would be a good Chancellor."

[Turn 0] Bot_2 voted Ja!
Reasoning: "I support this government. We need to establish a Liberal government to prevent the rise of Fascism."

[Turn 0] Bot_3 voted Ja!
Reasoning: "I support this government because I believe Bot_1 would make a good Chancellor."

[Turn 0] Bot_4 voted Nein!
Reasoning: "I am not yet comfortable supporting this government."

[Turn 0] Election for President Unsuspecting Human and Chancellor Bot_1: passed
Reasoning: "Votes: 3/5, Supported by ['Bot_1', 'Bot_2', 'Bot_3'], Opposed by ['Unsuspecting Human', 'Bot_4']"
```

### Using Your Custom Responder

1. First implement your responder:
```python
from responders.base import Responder, InputRequest
from typing import Dict, Any

class CustomResponder(Responder):
    def __init__(self, strategy: str = "default"):
        self.strategy = strategy

    def get_response(self, request: InputRequest) -> Dict[str, Any]:
        # Your implementation here

        # if you would not like to implement a custom formatter/renderer of the game context
        # call built-in formatter
        # returns the context str as shown in example
        formatted_context = GameStateTextFormatter.format_state(request.context, request.player_id) 

        pass
```

2. Create a function to handle responder creation:
```python
def create_custom_responder() -> Responder:
    return CustomResponder(strategy="aggressive)"
```

3. Set up the game with your responder:
```python
from pathlib import Path
from basilisk.main import setup_game, create_human_responder, create_ai_responder

# Define your players
player_configs = [
    {"name": "Alice", "type": "custom"},
    {"name": "Bob", "type": "ai"},
    {"name": "Charlie", "type": "human"}
]

def setup_custom_game() -> GameManager:
    # Setup responder creators with your custom type
    system_prompt_path = Path("responders/ollama/configs/system.txt")
    responder_creators = {
        "human": create_human_responder,
        "ai": create_ai_responder
        "custom": create_custom_responder # you may consider using lambdas to invoke create functions with given parameters
    }
    
    return GameManager(
        player_configs=player_configs,
        responder_creators=responder_creators,
        discussion_limit=2
    )

# Create and run game
game = setup_custom_game()
game.play_game()
```

This approach allows you to:
- Define custom creation logic for your responder
- Initialize with specific parameters
- Mix different responder types in a game
- Keep creation logic separate from game setup

## Quick Start

Check `basilisk/main.py`
for a sample game setup.

The current version is making use of Google Gemini, but you may easily switch out the LLM. However, if you use it as is make sure to provide GOOGLE_API_KEY in a `.env` file.

## Contributing

Contributions are welcome! Please ensure any pull requests:
1. Follow the existing code style
2. Update documentation as needed

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

## Disclaimer

This is an unofficial implementation of Secret Hitler intended for research purposes. Secret Hitler is a social deduction game designed by Mike Boxleiter, Tommy Maranges, and Max Temkin.