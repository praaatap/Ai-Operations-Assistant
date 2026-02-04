"""
News Tool - Fetch news articles using NewsAPI
"""
import os
import httpx
from typing import Any, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_tool import BaseTool


class NewsTool(BaseTool):
    """Tool for fetching news using NewsAPI"""
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @property
    def name(self) -> str:
        return "news"
    
    @property
    def description(self) -> str:
        return "Fetch latest news articles by topic, keyword, or category. Returns headlines, descriptions, and sources."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "action": {
                "type": "string",
                "description": "Action: 'headlines' for top headlines, 'search' to search articles",
                "required": True,
                "enum": ["headlines", "search"]
            },
            "query": {
                "type": "string",
                "description": "Search query or topic (e.g., 'technology', 'AI', 'climate change')",
                "required": False
            },
            "category": {
                "type": "string",
                "description": "News category for headlines: business, entertainment, health, science, sports, technology",
                "required": False
            },
            "country": {
                "type": "string",
                "description": "Country code for headlines (e.g., 'us', 'gb', 'in')",
                "required": False,
                "default": "us"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of articles to return (default: 5)",
                "required": False,
                "default": 5
            }
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Fetch news articles"""
        if not self.api_key:
            return {"error": "NEWS_API_KEY environment variable not set"}
        
        action = kwargs.get("action", "headlines")
        
        try:
            if action == "headlines":
                return await self._get_headlines(**kwargs)
            elif action == "search":
                return await self._search_articles(**kwargs)
            else:
                return {"error": f"Unknown action: {action}"}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return {"error": "Invalid NEWS_API_KEY"}
            elif e.response.status_code == 429:
                return {"error": "NewsAPI rate limit exceeded"}
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_headlines(self, **kwargs) -> Dict[str, Any]:
        """Get top headlines"""
        params = {
            "apiKey": self.api_key,
            "country": kwargs.get("country", "us"),
            "pageSize": kwargs.get("limit", 5)
        }
        
        category = kwargs.get("category")
        if category:
            params["category"] = category
        
        query = kwargs.get("query")
        if query:
            params["q"] = query
        
        response = await self.client.get(
            f"{self.BASE_URL}/top-headlines",
            params=params
        )
        response.raise_for_status()
        return self._format_response(response.json())
    
    async def _search_articles(self, **kwargs) -> Dict[str, Any]:
        """Search news articles"""
        query = kwargs.get("query")
        if not query:
            return {"error": "Query parameter is required for search"}
        
        response = await self.client.get(
            f"{self.BASE_URL}/everything",
            params={
                "apiKey": self.api_key,
                "q": query,
                "sortBy": "publishedAt",
                "pageSize": kwargs.get("limit", 5),
                "language": "en"
            }
        )
        response.raise_for_status()
        return self._format_response(response.json())
    
    def _format_response(self, data: Dict) -> Dict[str, Any]:
        """Format API response"""
        articles = []
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title", "No title"),
                "description": article.get("description", "No description"),
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt"),
                "author": article.get("author", "Unknown")
            })
        
        return {
            "success": True,
            "total_results": data.get("totalResults", 0),
            "articles": articles
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
