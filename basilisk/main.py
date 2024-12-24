from pathlib import Path
from typing import Dict, List, Callable, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from core.game_manager import GameManager, ResponderCreator
from responders import HumanResponder, LLMResponder, Responder

from dotenv import load_dotenv
import os

def init_llm() -> BaseChatModel:
    """Initialize LLM with environment configuration"""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
            
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-thinking-exp",  
        api_key=api_key,
        temperature=1.0,
        top_p=0.95,
        top_k=40,
        allow_unsafe_outputs=True
    )

def init_llm_local(model_name = "Qwen/Qwen2.5-3B-Instruct") -> BaseChatModel:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    class localLLM(BaseChatModel):
        def __init__(self, model_name):
            self.llm = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="bfloat16",
            device_map="auto"
            )
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        @property
        def _llm_type(self) -> str:
            return "qwen"

        def invoke(self, prompt):
            model_inputs = self.tokenizer([prompt], return_tensors="pt").to(self.llm.device)

            generated_ids = self.llm.generate(
                **model_inputs,
                max_new_tokens=1024
            )
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]

            response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

            return response
        
        def _generate(self, prompt):
            model_inputs = self.tokenizer([prompt], return_tensors="pt").to(self.llm.device)

            generated_ids = self.llm.generate(
                **model_inputs,
                max_new_tokens=1024
            )
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]

            response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

            return response

    return localLLM(model_name)

def create_human_responder(player_id: str) -> Responder:
    return HumanResponder(player_id)

def create_ai_responder(
    player_id: str,
    llm: BaseChatModel,
    config_dir: str = "responders/llm/configs",
) -> Responder:
    return LLMResponder(
        player_id=player_id,
        system_prompt_path=Path(config_dir) / "system.txt",
        llm=llm,
        memory_size=10,
        max_retries=3,
        show_internal_thinking=True,
        debug=False
    )

def setup_game(
    player_configs: List[Dict[str, str]],
    llm: Optional[BaseChatModel] = None,
    discussion_limit: int = 2
) -> GameManager:
    """Setup game with player configs."""
    if any(pc["type"] == "ai" for pc in player_configs) and llm is None:
        raise ValueError("LLM required for AI players")
        
    responder_creators = {
        "human": create_human_responder,
        "ai": lambda pid: create_ai_responder(pid, llm)
    }
    
    return GameManager(
        player_configs=player_configs,
        responder_creators=responder_creators,
        discussion_limit=discussion_limit
    )

# Original console game setup functions
def setup_ai_game(
    player_count: int = 5,
    discussion_limit: int = 2,
    llm: Optional[BaseChatModel] = None
) -> GameManager:
    """Setup an AI-only game"""
    if llm is None:
        llm = init_llm()
        
    player_configs = [
        {
            "name": f"Player_{i+1}",
            "type": "ai"
        }
        for i in range(player_count)
    ]
    
    return setup_game(
        player_configs=player_configs,
        llm=llm,
        discussion_limit=discussion_limit
    )
    
def setup_human_vs_ai_game(
    human_player_name: str,
    ai_player_count: int = 4,
    discussion_limit: int = 2,
    llm: Optional[BaseChatModel] = None
) -> GameManager:
    """Setup a console-based human vs AI game"""
    if llm is None:
        llm = init_llm()
        
    player_configs = [
        {
            "name": human_player_name,
            "type": "human"
        }
    ]
    player_configs += [
        {
            "name": f"Bot_{i+1}",
            "type": "ai"
        }
        for i in range(ai_player_count)
    ]
    
    return setup_game(
        player_configs=player_configs,
        llm=llm,
        discussion_limit=discussion_limit
    )
    
if __name__ == "__main__":
    # Run console-based game when script is run directly
    try:
        # Initialize LLM once for reuse
        llm = init_llm_local()
        
        # Create and run human vs AI game
        game = setup_human_vs_ai_game(
            human_player_name="Human Player",
            ai_player_count=4,
            discussion_limit=2,
            llm=llm
        )
        
        game.play_game()
        
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        print(f"\nError: {str(e)}")