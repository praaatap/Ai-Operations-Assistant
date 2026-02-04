"""
Base Tool - Abstract interface for all tools
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """Abstract base class for all tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name identifier"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """
        JSON schema describing the tool's parameters.
        Format: {"param_name": {"type": "string", "description": "...", "required": True}}
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Returns:
            Dictionary with results or error information
        """
        pass
    
    def to_schema(self) -> Dict[str, Any]:
        """Convert tool to schema format for LLM"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
