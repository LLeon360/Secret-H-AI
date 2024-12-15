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
│   └── ollama/
│       ├── __init__.py
│       ├── responder.py  # Ollama LLM responder
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
                - context: Complete game state as text
                - fields: Required response fields
                - example: Example response format
        
        Returns:
            Dictionary matching the format specified in request.fields
        """
        pass
```

### Input Request Format

Each request contains:

```python
@dataclass
class InputRequest:
    input_type: InputType  # e.g., VOTE, POLICY_SELECTION
    player_id: str        # ID of player making decision
    context: str          # Formatted game state
    fields: List[InputField]  # Required response fields
    example: ExampleResponse  # Example of valid response
```

Example request for policy selection:
```python
request = InputRequest(
    input_type=InputType.POLICY_SELECTION,
    player_id="p1",
    context="[Game state text]",
    fields=[
        InputField(
            name="policy",
            field_type="choice",
            prompt="Choose policy to discard:",
            options=["Liberal", "Fascist"],
            required=True
        ),
        InputField(
            name="claimed_policy",
            field_type="choice",
            prompt="What policy to claim?",
            options=["liberal", "fascist", "undisclosed"],
            required=False,
            default=2
        ),
        InputField(
            name="justification",
            field_type="text",
            prompt="Explain choice:",
            required=True
        )
    ],
    example=ExampleResponse(
        values={
            "policy": 0,
            "claimed_policy": 2,
            "justification": "Strategic explanation"
        }
    )
)
```

### Game State Context

The context provided in each request looks like:

```
==================== Game Status ====================

Turn 2
You are Charlie
Your Role: Fascist
Current Phase: Nominating Chancellor

Policies Enacted:
Liberal Track: 🔵⚪⚪⚪⚪ (1/5)
Fascist Track: ⚪⚪⚪⚪⚪⚪ (0/6)

Current Government:
President: Charlie

Last Government: Bob (P), Eve (C)

Players:
  • Alice
  • Bob
  • Charlie (President)
  • David
  • Eve (Previously Nominated as Chancellor)

As a Fascist, you know:
  • David is Hitler

==================== Recent Events ====================

[Turn 1] David voted Nein!
Reasoning: "I don't trust this government"

[Turn 1] Election for President Bob and Chancellor Eve: passed
Reasoning: "Votes: 4/5"

[Turn 1] President Bob claims to have discarded a fascist policy
[Turn 1] Chancellor Eve enacted a liberal policy
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