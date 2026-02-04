"""
Wikipedia Tool - Search and get article summaries from Wikipedia

This tool uses the free Wikipedia API (no API key required).
"""
import httpx
from typing import Any, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_tool import BaseTool


class WikipediaTool(BaseTool):
    """Tool for searching Wikipedia and getting article summaries"""
    
    BASE_URL = "https://en.wikipedia.org/api/rest_v1"
    SEARCH_URL = "https://en.wikipedia.org/w/api.php"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "AI-Ops-Assistant/2.0 (https://github.com/ai-ops; contact@ai-ops.dev) httpx/0.26",
                "Accept": "application/json"
            },
            timeout=30.0
        )
    
    @property
    def name(self) -> str:
        return "wikipedia"
    
    @property
    def description(self) -> str:
        return "Search Wikipedia articles and get summaries. Use for getting information about topics, people, places, concepts, etc."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "action": {
                "type": "string",
                "description": "Action to perform: 'search' to find articles, 'summary' to get article summary",
                "required": True,
                "enum": ["search", "summary"]
            },
            "query": {
                "type": "string",
                "description": "Search query or article title",
                "required": True
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of search results (default: 5)",
                "required": False,
                "default": 5
            }
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute Wikipedia API request"""
        action = kwargs.get("action", "search")
        
        try:
            if action == "search":
                return await self._search(**kwargs)
            elif action == "summary":
                return await self._get_summary(**kwargs)
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _search(self, **kwargs) -> Dict[str, Any]:
        """Search Wikipedia for articles"""
        query = kwargs.get("query")
        if not query:
            return {"error": "Query parameter is required"}
        
        try:
            limit = int(kwargs.get("limit", 5))
        except (ValueError, TypeError):
            limit = 5
        
        response = await self.client.get(
            self.SEARCH_URL,
            params={
                "action": "opensearch",
                "search": query,
                "limit": limit,
                "format": "json"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # OpenSearch returns [query, [titles], [descriptions], [urls]]
        titles = data[1] if len(data) > 1 else []
        descriptions = data[2] if len(data) > 2 else []
        urls = data[3] if len(data) > 3 else []
        
        results = []
        for i, title in enumerate(titles):
            results.append({
                "title": title,
                "description": descriptions[i] if i < len(descriptions) else "",
                "url": urls[i] if i < len(urls) else ""
            })
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    
    async def _get_summary(self, **kwargs) -> Dict[str, Any]:
        """Get summary of a Wikipedia article"""
        query = kwargs.get("query")
        if not query:
            return {"error": "Query parameter is required"}
        
        # Convert query to URL-safe format
        title = query.replace(" ", "_")
        
        response = await self.client.get(
            f"{self.BASE_URL}/page/summary/{title}"
        )
        
        if response.status_code == 404:
            return {"error": f"Article '{query}' not found"}
        
        response.raise_for_status()
        data = response.json()
        
        return {
            "success": True,
            "article": {
                "title": data.get("title", query),
                "description": data.get("description", ""),
                "extract": data.get("extract", "No summary available"),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "thumbnail": data.get("thumbnail", {}).get("source", None)
            }
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
