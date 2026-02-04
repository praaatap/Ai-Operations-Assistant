"""
Base Agent - Abstract base class for all agents
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.client import LLMClient


class BaseAgent(ABC):
    """Abstract base class for all agents in the system"""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the agent with an LLM client.
        
        Args:
            llm_client: LLM client for generating responses
        """
        self.llm = llm_client
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name identifier"""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt that defines the agent's role and behavior"""
        pass
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """
        Process input and return output.
        
        Args:
            input_data: Input data for the agent to process
            
        Returns:
            Processed output
        """
        pass
    
    def _generate(self, prompt: str) -> str:
        """Generate text response from LLM"""
        return self.llm.generate(prompt, self.system_prompt)
    
    def _generate_json(self, prompt: str) -> Dict[str, Any]:
        """Generate JSON response from LLM"""
        return self.llm.generate_json(prompt, self.system_prompt)
