from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import re
from langchain_core.language_models.chat_models import BaseChatModel

from ..base import Responder, InputRequest, InputField

@dataclass
class Memory:
    """Simple memory buffer for storing past events/decisions"""
    max_items: int = 10
    entries: List[str] = field(default_factory=list)
    
    def add(self, entry: str):
        self.entries.append(entry)
        if len(self.entries) > self.max_items:
            self.entries.pop(0)
    
    def get_recent(self, limit: Optional[int] = None) -> str:
        entries = self.entries[-limit:] if limit else self.entries
        return "\n".join(entries) if entries else "No previous memories."

class LLMResponder(Responder):
    def __init__(self, 
                 system_prompt_path: Optional[str],
                 llm: BaseChatModel,
                 memory_size: int,
                 max_retries: int = 3,
                 show_internal_thinking: bool = False,
                 debug: bool = False):
        self.llm = llm
        self.memory = Memory(max_items=memory_size)
        self.max_retries = max_retries
        self.memory_size = memory_size
        self.show_internal_thinking = show_internal_thinking
        self.debug = debug
        
        # Load system prompt
        self.system_prompt = ""
        if system_prompt_path:
            path = Path(system_prompt_path)
            if path.exists():
                self.system_prompt = path.read_text()
    
    def _build_prompt(self, request: InputRequest) -> str:
        """Build prompt with system instructions, memory, context, and required format"""
        sections = []
        
        # Add system prompt if exists
        if self.system_prompt:
            sections.append(f"System Instructions:\n{self.system_prompt}\n")
            
        # Add memory context
        sections.append(f"Recent Events:\n{self.memory.get_recent(self.memory_size)}\n")
        
        # Add current context
        sections.append(f"Current Situation:\n{request.context}\n")
        
        # Add prompt details
        sections.append(f"You are currently considering the following decisions:\n")
        
        for field in request.fields:
            sections.append(f"- {field.prompt}")
            if field.required:
                sections.append("Required: Yes")
            match field.field_type:
                case "choice":
                    sections.append(f"This is a choice, please choose from the following options by selecting an index (0-indexed):\n")
                    sections.append(f"{''.join(f"{num}. {option}" for num, option in enumerate(field.options))}")
                case "text":
                    sections.append("Type: Text Response (Provide a string)")
                case "boolean":
                    sections.append("Type: Boolean Response (Provide True or False)")
        
        # Add required response format
        sections.append(
            "Please provide your response in the following format:\n\n"
            "<memory_update>\n"
            "Summarize the current situation and any important observations\n"
            "</memory_update>\n\n"
            
            "<reasoning>\n"
            "Explain your strategic thinking and analysis\n"
            "</reasoning>\n\n"
            
            "<decision>\n"
            f"Provide your decision in this JSON format:\n{json.dumps(request.example.values, indent=2)}\n"
            "</decision>"
        )
        
        return "\n".join(sections)
    
    def _extract_section(self, content: str, section: str) -> Optional[str]:
        """Extract content from a section"""
        pattern = f"<{section}>(.*?)</{section}>"
        if match := re.search(pattern, content, re.DOTALL):
            return match.group(1).strip()
        return None
    
    def _parse_decision(self, decision_str: str) -> Dict[str, Any]:
        """Parse and validate decision JSON"""
        try:
            return json.loads(decision_str)
        except json.JSONDecodeError:
            raise ValueError("Invalid decision JSON format")
        
    def _validate_decision(self, decision: Dict[str, Any], fields: List[InputField]) -> bool:
        """Validate the decision JSON against the required fields and their types"""
        for field in fields:
            if field.required and field.name not in decision:
                return False
            if field.name in decision:
                value = decision[field.name]
                if field.field_type == "choice" and value not in range(len(field.options)):
                    return False
                if field.field_type == "boolean" and not isinstance(value, bool):
                    return False
                if field.field_type == "text" and not isinstance(value, str):
                    return False
        return True
    
    def get_response(self, request: InputRequest) -> Dict[str, Any]:
        """Get response from model with retries"""        
        for attempt in range(self.max_retries):
            try:
                # Get model response
                prompt = self._build_prompt(request)
                response = self.llm.invoke([prompt]).content
                
                if self.show_internal_thinking:
                    print(response)
                
                # Extract sections
                if memory_update := self._extract_section(response, "memory_update"):
                    self.memory.add(memory_update)
                
                if decision_str := self._extract_section(response, "decision"):
                    decision = self._parse_decision(decision_str)
                    
                    # Validate required fields and their types
                    if not self._validate_decision(decision, request.fields):
                        if self.debug:
                            print(f"Invalid decision format or missing required fields: {decision}")
                        raise ValueError("Invalid decision format or missing required fields")

                    return decision
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise ValueError(f"Failed to get valid response after {self.max_retries} attempts: {str(e)}")
                continue