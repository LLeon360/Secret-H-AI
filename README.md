# Secret Hitler Game State Manager

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

class AIResponder(Responder):
    def get_response(self, request: InputRequest) -> Dict[str, Any]:
        # Process context and generate response based on input_type
        # Return response matching response_format schema
        pass
```

2. Register AI players:

```python
player_types = {
    "p1": "human",
    "p2": "ai",
    "p3": "ai",
    "p4": "human",
    "p5": "ai"
}

# Register custom responder for AI players
for pid, ptype in player_types.items():
    if ptype == "ai":
        game.input_handler.register_responder(pid, AIResponder())
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

#### Example 1
Example context format:
```
=== Input Request ===

Context:

==================== Game Status ====================
=== Input Request ===

Context:

==================== Game Status ====================

You are Eve
Your Role: Fascist
Current Phase: Voting

Policies Enacted:
Liberal Track: ⚪⚪⚪⚪⚪ (0/5)
Fascist Track: ⚪⚪⚪⚪⚪⚪ (0/6)

Current Government:
President: Alice
Nominated Chancellor: Bob

Players:
  • Alice (President)
  • Bob (Nominated)
  • Charlie
  • David
  • Eve

You know the following players are Fascists:
  • Alice, Eve

==================== Recent Events ====================

System Game started with 5 players
Reasoning: "Game initialized"

Alice nominated Bob as Chancellor
Reasoning: "Well game's just started"

```

##### Prompt

```
Prompt: Vote on the proposed government

Options:
1. Ja!
2. Nein!

Enter your choice (number): 2

Enter justification: erm
```

#### Example 2
```
=== Input Request ===

Context:

==================== Game Status ====================

You are Bob
Your Role: Liberal
Current Phase: Chancellor Discard

Policies Enacted:
Liberal Track: ⚪⚪⚪⚪⚪ (0/5)
Fascist Track: ⚪⚪⚪⚪⚪⚪ (0/6)

Current Government:
President: Alice
Chancellor: Bob

Last Government: Alice (P), Bob (C)

Players:
  • Alice (President)
  • Bob (Chancellor)
  • Charlie
  • David
  • Eve

==================== Recent Events ====================

Bob voted Nein!
Reasoning: "I dont trust myself"

Charlie voted Ja!
Reasoning: "meh"

David voted Ja!
Reasoning: "jafsdhljasdkfha"

Eve voted Nein!
Reasoning: "erm"

System election for President Alice and Chancellor Bob, Result passed
Reasoning: "Votes: 3/5, Supported by ['Alice', 'Charlie', 'David'], Opposed by ['Bob', 'Eve']"

```

##### Prompt
```


Prompt: Choose a policy to enact

Options:
1. Policy: fascist
2. Policy: liberal

Enter your choice (number):

```

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
1. Include appropriate tests
2. Follow the existing code style
3. Update documentation as needed

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This is an unofficial implementation of Secret Hitler intended for research purposes. Secret Hitler is a social deduction game designed by Mike Boxleiter, Tommy Maranges, and Max Temkin.