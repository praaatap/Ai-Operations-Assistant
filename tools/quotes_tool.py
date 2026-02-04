"""
Quotes Tool - Get inspirational and famous quotes

This tool uses free quote APIs (no API key required).
"""
import httpx
from typing import Any, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_tool import BaseTool


class QuotesTool(BaseTool):
    """Tool for fetching inspirational and famous quotes"""
    
    QUOTES_API_URL = "https://api.quotable.io"
    ZEN_QUOTES_URL = "https://zenquotes.io/api"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={"User-Agent": "AI-Ops-Assistant"},
            timeout=30.0
        )
    
    @property
    def name(self) -> str:
        return "quotes"
    
    @property
    def description(self) -> str:
        return "Get inspirational quotes, famous quotes, or quotes by specific authors. Great for motivation and adding depth to responses."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "action": {
                "type": "string",
                "description": "Action: 'random' for random quotes, 'search' to search by keyword, 'author' to get quotes by author",
                "required": True,
                "enum": ["random", "search", "author", "today"]
            },
            "query": {
                "type": "string",
                "description": "Search query or author name (required for 'search' and 'author' actions)",
                "required": False
            },
            "count": {
                "type": "integer",
                "description": "Number of quotes to fetch (default: 3, max: 10)",
                "required": False,
                "default": 3
            }
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute quotes API request"""
        action = kwargs.get("action", "random")
        
        try:
            if action == "random":
                return await self._get_random_quotes(**kwargs)
            elif action == "today":
                return await self._get_quote_of_day()
            elif action == "search":
                return await self._search_quotes(**kwargs)
            elif action == "author":
                return await self._get_author_quotes(**kwargs)
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_random_quotes(self, **kwargs) -> Dict[str, Any]:
        """Get random quotes from DummyJSON"""
        try:
            count = int(kwargs.get("count", 3))
        except (ValueError, TypeError):
            count = 3
        count = min(count, 10)
        
        # DummyJSON returns 30 by default, we can pick random ones or just take top N
        response = await self.client.get("https://dummyjson.com/quotes")
        response.raise_for_status()
        data = response.json()
        
        all_quotes = data.get("quotes", [])
        import random
        selected_quotes = random.sample(all_quotes, min(count, len(all_quotes)))
        
        quotes = []
        for item in selected_quotes:
            quotes.append({
                "content": item.get("quote", ""),
                "author": item.get("author", "Unknown"),
                "tags": []
            })
        
        return {
            "success": True,
            "quotes": quotes,
            "count": len(quotes)
        }
    
    async def _get_quote_of_day(self) -> Dict[str, Any]:
        """Get quote of the day from ZenQuotes"""
        response = await self.client.get(f"{self.ZEN_QUOTES_URL}/today")
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            quote = data[0]
            return {
                "success": True,
                "quote": {
                    "content": quote.get("q", ""),
                    "author": quote.get("a", "Unknown")
                },
                "type": "quote_of_the_day"
            }
        
        return {"error": "Could not fetch quote of the day"}
    
    async def _search_quotes(self, **kwargs) -> Dict[str, Any]:
        """Search quotes by keyword"""
        query = kwargs.get("query")
        if not query:
            return {"error": "Query parameter is required for search"}
        
        try:
            count = int(kwargs.get("count", 3))
        except (ValueError, TypeError):
            count = 3
        count = min(count, 10)
        
        response = await self.client.get(
            f"{self.QUOTES_API_URL}/search/quotes",
            params={"query": query, "limit": count}
        )
        response.raise_for_status()
        data = response.json()
        
        quotes = []
        for item in data.get("results", []):
            quotes.append({
                "content": item.get("content", ""),
                "author": item.get("author", "Unknown"),
                "tags": item.get("tags", [])
            })
        
        return {
            "success": True,
            "query": query,
            "quotes": quotes,
            "count": len(quotes)
        }
    
    async def _get_author_quotes(self, **kwargs) -> Dict[str, Any]:
        """Get quotes by a specific author"""
        author = kwargs.get("query")
        if not author:
            return {"error": "Author name (query parameter) is required"}
        
        try:
            count = int(kwargs.get("count", 3))
        except (ValueError, TypeError):
            count = 3
        count = min(count, 10)
        
        response = await self.client.get(
            f"{self.QUOTES_API_URL}/quotes",
            params={"author": author, "limit": count}
        )
        response.raise_for_status()
        data = response.json()
        
        quotes = []
        for item in data.get("results", []):
            quotes.append({
                "content": item.get("content", ""),
                "author": item.get("author", "Unknown"),
                "tags": item.get("tags", [])
            })
        
        return {
            "success": True,
            "author": author,
            "quotes": quotes,
            "count": len(quotes)
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
