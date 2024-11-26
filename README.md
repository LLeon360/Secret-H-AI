# Basilisk - Secret Hitler Game State Manager for Humans and LLMs 

A Python framework for simulating and tracking the state of Secret Hitler games, designed to support both human players and Language Learning Models (LLMs) through a structured input/output interface.

## Overview

This project provides a robust game state management system for Secret Hitler, with special consideration for AI players. It features:

- Complete game state tracking and validation
- Natural language formatting of game state for LLM consumption
- Structured JSON-based input handling
- Support for mixed human/AI players
- Event logging and game history tracking

## Project Structure

```
├── game_state.py      # Core game state management and rules
├── game_manager.py    # High-level game flow and player interaction
├── input_handler.py   # Input processing and validation
└── main.py           # Example game initialization
```

## Key Components

### Game State (`game_state.py`)

The `SecretHitler` class manages the core game state, including:
- Player roles and status
- Policy deck and discard pile
- Government positions
- Game phase tracking
- Event logging
- Private information management

### Game Manager (`game_manager.py`)

`GameManager` handles the high-level game flow:
- Turn management
- Player input collection
- State formatting for players
- Discussion rounds
- Game event processing

### Input Handler (`input_handler.py`)

Provides a flexible system for processing player inputs:
- Abstract `Responder` interface for different player types
- Input validation and formatting
- Support for both human and AI players
- Structured response formats

## Usage

### Basic Setup

```python
from game_manager import GameManager

# Initialize players
player_ids = ["p1", "p2", "p3", "p4", "p5"]
player_names = ["Alice", "Bob", "Charlie", "David", "Eve"]
player_types = {pid: "human" for pid in player_ids}

# Create game instance
game = GameManager(player_ids, player_names, player_types)
game.play_game()
```

### Creating an AI Player

1. Implement the `Responder` interface:

```python
from input_handler import Responder, InputRequest

class ModelResponder(Responder):
    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt

    def get_response(self, request: InputRequest) -> Dict[str, Any]:
        """Format request for model and parse response"""
        # This would be implemented with actual LLM integration
        # For now, just return a mock response
        raise NotImplementedError("Model responder not yet implemented")

```

2. Register AI players:

In `GameManager` `__init__`
```python
class GameManager:
    def __init__(self, player_ids: List[str], player_names: List[str], player_types: Dict[str, str],
                 discussion_limit: int = 1):
        self.game = SecretHitler(player_ids, player_names)
        self.game.discussion_limit = discussion_limit
        
        self.input_handler = InputHandler()
        self.current_event_index = len(self.game.game_events) - 1
        
        # Register responders for each player
        for pid in player_ids:
            if player_types[pid] == "human":
                self.input_handler.register_responder(pid, HumanResponder())
            else:
                self.input_handler.register_responder(pid, ModelResponder())
```

#### Example HumanResponder

The `HumanResponder` `get_response` breaks down the required fields and breaks them into prompts. 
An LLM responder may instead pass in the context with an API call prompting for a JSON formatted response and validate the response structure. You may prompt for additional chain of thought reasoning so long as you are able to parse out the response format into an appropriate response dict.

```python
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
```

## Input/Output Format

### Game State Context 

The game state is formatted as natural language text, including:
- Current game phase
- Policy track status
- Government positions
- Player status
- Recent game events
- Private information (role-specific)

### Input Requests

Input requests are structured with:
- Input type (e.g., nomination, vote, policy selection)
- Context (formatted game state)
- Prompt
- Response format specification
- Available options (if applicable)

Example response format:
```json
{
    "choice": 0,
    "justification": "I trust this player to make good decisions"
}
```

### Examples

#### Example 1

##### Context

```
=== Input Request ===

Context:

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
Reasoning: "sus"

[Turn 1] Eve voted Ja!
Reasoning: "1"

[Turn 1] Election for President Bob and Chancellor Eve: passed
Reasoning: "Votes: 4/5, Supported by ['Alice', 'Bob', 'Charlie', 'Eve'], Opposed by ['David']"

[Turn 1] President Bob claims to have discarded a fascist policy
Reasoning: "im cool like that"

[Turn 1] Chancellor Eve enacted a liberal policy (claims to have discarded a liberal policy)
Reasoning: "yay"

```

##### Prompt

```

Choose a chancellor candidate:

Options:
1. Alice
2. David

Enter your choice (number): 2

Explain your nomination:

Enter your response: idk just a hunch good guy

```
<details>
  <summary>Example 2</summary>

#### Example 2

##### Context

```
=== Input Request ===

Context:

==================== Game Status ====================

Turn 2
You are Bob
Your Role: Liberal
Current Phase: Voting

Policies Enacted:
Liberal Track: 🔵⚪⚪⚪⚪ (1/5)
Fascist Track: ⚪⚪⚪⚪⚪⚪ (0/6)

Current Government:
President: Charlie
Nominated Chancellor: David

Last Government: Bob (P), Eve (C)

Players:
  • Alice
  • Bob
  • Charlie (President)
  • David (Nominated)
  • Eve

Private Information:

Policy choice as President (1 turns ago):
Government: You as President with Eve as Chancellor
Policy counts were: Liberal 0, Fascist 0
You saw: liberal, liberal, liberal
You discarded: liberal
You claimed to discard: fascist
You passed: liberal, liberal to Chancellor
(This information expires in 2 turns)

==================== Recent Events ====================

[Turn 1] Eve voted Ja!
Reasoning: "1"

[Turn 1] Election for President Bob and Chancellor Eve: passed
Reasoning: "Votes: 4/5, Supported by ['Alice', 'Bob', 'Charlie', 'Eve'], Opposed by ['David']"

[Turn 1] President Bob claims to have discarded a fascist policy
Reasoning: "im cool like that"

[Turn 1] Chancellor Eve enacted a liberal policy (claims to have discarded a liberal policy)
Reasoning: "yay"

[Turn 2] Charlie nominated David as Chancellor
Reasoning: "idk just a hunch good guy"
```

##### Prompt

```
Vote on the proposed government:

Options:
1. Ja!
2. Nein!

Enter your choice (number): 1

Explain your vote:

Enter your response:
```
</details>

## Events and Logging

The system maintains a detailed log of game events, including:
- Government formations
- Votes
- Policy enactments
- Power actions
- Player discussions

Events are formatted for both human readability and AI processing.

## Contributing

Contributions are welcome! Please ensure any pull requests:
1. Include appropriate tests (don't actually have a testing framework yet X_X)
2. Follow the existing code style
3. Update documentation as needed

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

## Disclaimer

This is an unofficial implementation of Secret Hitler intended for research purposes. Secret Hitler is a social deduction game designed by Mike Boxleiter, Tommy Maranges, and Max Temkin.