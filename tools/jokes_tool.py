"""
Jokes Tool - Get random jokes from various categories

This tool uses free joke APIs (no API key required).
"""
import httpx
from typing import Any, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_tool import BaseTool


class JokesTool(BaseTool):
    """Tool for fetching random jokes"""
    
    JOKE_API_URL = "https://v2.jokeapi.dev/joke"
    DAD_JOKE_URL = "https://icanhazdadjoke.com"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={"User-Agent": "AI-Ops-Assistant"},
            timeout=30.0
        )
    
    @property
    def name(self) -> str:
        return "jokes"
    
    @property
    def description(self) -> str:
        return "Get random jokes. Categories include programming, general, dad jokes, puns, etc. Great for adding humor to responses."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "action": {
                "type": "string",
                "description": "Action: 'random' for any joke, 'programming' for programming jokes, 'dad' for dad jokes",
                "required": True,
                "enum": ["random", "programming", "dad", "pun"]
            },
            "count": {
                "type": "integer",
                "description": "Number of jokes to fetch (default: 1, max: 5)",
                "required": False,
                "default": 1
            }
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute joke API request"""
        action = kwargs.get("action", "random")
        try:
            count = int(kwargs.get("count", 1))
        except (ValueError, TypeError):
            count = 1
            
        count = min(count, 5)
        
        try:
            if action == "dad":
                return await self._get_dad_jokes(count)
            else:
                return await self._get_jokes(action, count)
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_jokes(self, category: str, count: int) -> Dict[str, Any]:
        """Get jokes from JokeAPI"""
        # Map actions to categories
        category_map = {
            "random": "Any",
            "programming": "Programming",
            "pun": "Pun"
        }
        cat = category_map.get(category, "Any")
        
        jokes = []
        for _ in range(count):
            response = await self.client.get(
                f"{self.JOKE_API_URL}/{cat}",
                params={"safe-mode": "true"}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("error"):
                continue
            
            if data.get("type") == "twopart":
                joke_text = f"{data.get('setup', '')} ... {data.get('delivery', '')}"
            else:
                joke_text = data.get("joke", "")
            
            jokes.append({
                "joke": joke_text,
                "category": data.get("category", "General"),
                "type": data.get("type", "single")
            })
        
        return {
            "success": True,
            "jokes": jokes,
            "count": len(jokes)
        }
    
    async def _get_dad_jokes(self, count: int) -> Dict[str, Any]:
        """Get dad jokes"""
        jokes = []
        
        for _ in range(count):
            response = await self.client.get(
                self.DAD_JOKE_URL,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            
            jokes.append({
                "joke": data.get("joke", ""),
                "category": "Dad Joke",
                "type": "single"
            })
        
        return {
            "success": True,
            "jokes": jokes,
            "count": len(jokes)
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
