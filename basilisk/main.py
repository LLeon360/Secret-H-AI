# main.py
from pathlib import Path
from typing import Dict, List, Callable
from core.game_manager import GameManager, ResponderCreator
from responders import HumanResponder, OllamaResponder, Responder

def create_human_responder() -> Responder:
    return HumanResponder()

def create_ai_responder(
    config_dir: str = "responders/ollama/configs",
    model_name: str = "llama2"
) -> Responder:
    system_prompt_path = Path(config_dir) / "system.txt"
    return OllamaResponder(
        system_prompt_path=system_prompt_path,
        model_name=model_name
    )

def setup_game(
    player_configs: List[Dict[str, str]],
    discussion_limit: int = 2
) -> GameManager:
    """Setup game with player configs.
    
    Args:
        player_configs: List of dicts with keys:
            - name: Player name
            - type: Player type ("human" or "ai")
        discussion_limit: Max discussion messages per player
    """
    responder_creators = {
        "human": create_human_responder,
        "ai": create_ai_responder
    }
    
    return GameManager(
        player_configs=player_configs,
        responder_creators=responder_creators,
        discussion_limit=discussion_limit
    )

def setup_ai_game(
    player_count: int = 5,
    discussion_limit: int = 2
) -> GameManager:
    """Convenience function to setup an AI-only game"""
    player_configs = [
        {
            "name": f"Player_{i+1}",
            "type": "ai"
        }
        for i in range(player_count)
    ]
    
    return setup_game(
        player_configs=player_configs,
        discussion_limit=discussion_limit
    )
    
# if __name__ == "__main__":
#     # Run AI-only game
#     game = setup_ai_game()
#     game.play_game()