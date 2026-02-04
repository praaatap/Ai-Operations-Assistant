"""
GitHub Tool - Search repositories and fetch repository details with caching
"""
import os
import httpx
from typing import Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_tool import BaseTool

# Import cache utilities
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cache import cached


class GitHubTool(BaseTool):
    """Tool for interacting with GitHub API with caching support"""
    
    BASE_URL = "https://api.github.com"
    CACHE_TTL = int(os.getenv("CACHE_TTL_GITHUB", 600))  # 10 minutes default
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AI-Ops-Assistant"
            },
            timeout=30.0
        )
    
    @property
    def name(self) -> str:
        return "github"
    
    @property
    def description(self) -> str:
        return "Search GitHub repositories, get repository details including stars, forks, and descriptions. Use for finding open source projects, trending repos, or specific repository information."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "action": {
                "type": "string",
                "description": "Action to perform: 'search' to search repositories, 'get_repo' to get specific repo details",
                "required": True,
                "enum": ["search", "get_repo"]
            },
            "query": {
                "type": "string",
                "description": "Search query for repositories (required for 'search' action)",
                "required": False
            },
            "owner": {
                "type": "string",
                "description": "Repository owner (required for 'get_repo' action)",
                "required": False
            },
            "repo": {
                "type": "string",
                "description": "Repository name (required for 'get_repo' action)",
                "required": False
            },
            "sort": {
                "type": "string",
                "description": "Sort search results by: 'stars', 'forks', 'updated'",
                "required": False,
                "default": "stars"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 5)",
                "required": False,
                "default": 5
            }
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute GitHub API request"""
        action = kwargs.get("action", "search")
        
        try:
            if action == "search":
                return await self._search_repos(**kwargs)
            elif action == "get_repo":
                return await self._get_repo(**kwargs)
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}
    
    @cached(prefix="github_search", ttl_seconds=600)
    async def _search_repos(self, **kwargs) -> Dict[str, Any]:
        """Search GitHub repositories with caching"""
        query = kwargs.get("query")
        if not query:
            return {"error": "Query parameter is required for search"}
        
        sort = kwargs.get("sort", "stars")
        limit = kwargs.get("limit", 5)
        
        response = await self.client.get(
            f"{self.BASE_URL}/search/repositories",
            params={
                "q": query,
                "sort": sort,
                "order": "desc",
                "per_page": limit
            }
        )
        response.raise_for_status()
        data = response.json()
        
        repos = []
        for repo in data.get("items", [])[:limit]:
            repos.append({
                "name": repo["full_name"],
                "description": repo.get("description", "No description"),
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "language": repo.get("language", "Unknown"),
                "url": repo["html_url"],
                "updated_at": repo["updated_at"]
            })
        
        return {
            "success": True,
            "total_count": data.get("total_count", 0),
            "repositories": repos,
            "cached": False  # Will be True when retrieved from cache
        }
    
    @cached(prefix="github_repo", ttl_seconds=600)
    async def _get_repo(self, **kwargs) -> Dict[str, Any]:
        """Get specific repository details with caching"""
        owner = kwargs.get("owner")
        repo = kwargs.get("repo")
        
        if not owner or not repo:
            return {"error": "Owner and repo parameters are required"}
        
        response = await self.client.get(f"{self.BASE_URL}/repos/{owner}/{repo}")
        response.raise_for_status()
        data = response.json()
        
        return {
            "success": True,
            "repository": {
                "name": data["full_name"],
                "description": data.get("description", "No description"),
                "stars": data["stargazers_count"],
                "forks": data["forks_count"],
                "language": data.get("language", "Unknown"),
                "url": data["html_url"],
                "open_issues": data["open_issues_count"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
                "topics": data.get("topics", [])
            },
            "cached": False
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
