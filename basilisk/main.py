# main.py
from pathlib import Path
from typing import Dict, List, Callable
from core.game_manager import GameManager, ResponderCreator
from responders import HumanResponder, LLMResponder, Responder

from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv
import os

def create_human_responder() -> Responder:
    return HumanResponder()

def create_ai_responder(
    config_dir: str = "responders/ollama/configs",
    model_name: str = "llama2"
) -> Responder:
    system_prompt_path = Path(config_dir) / "system.txt"
    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        api_key=google_api_key,
        temperature=0.7,  # Adjust the temperature as needed
        allow_unsafe_outputs=True  # Allow unsafe outputs
    )
    return LLMResponder(
        system_prompt_path=system_prompt_path,
        llm = llm,
        memory_size = 10,
        max_retries = 3,
        show_internal_thinking = False,
        debug = False
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
    
def setup_human_vs_ai_game(
    human_player_name: str,
    ai_player_count: int = 4,
    discussion_limit: int = 2
) -> GameManager:
    """Convenience function to setup a human vs AI game"""
    player_configs = [
        {
            "name": human_player_name,
            "type": "human"
        }]
    player_configs += [
        {
            "name": f"Bot_{i+1}",
            "type": "ai"
        }
        for i in range(ai_player_count)
    ]
    
    return setup_game(
        player_configs=player_configs,
        discussion_limit=discussion_limit
    )    

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Access the GOOGLE_API_KEY
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    # Run AI-only game
    game = setup_human_vs_ai_game(human_player_name="Unsuspecting Human", 
                                  ai_player_count=4, 
                                  discussion_limit=0)
    game.play_game()