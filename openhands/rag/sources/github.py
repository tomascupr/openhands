"""
GitHub code examples source adapter.
"""
from typing import Dict, List, Any

from openhands.core.logger import openhands_logger as logger
from openhands.rag.sources.base import CodeDocumentationSource
from openhands.rag.sources.web_search import WebSearchSource


class GitHubCodeExamplesSource(CodeDocumentationSource):
    """Retrieves code examples from GitHub repositories."""
    
    def __init__(self):
        """Initialize the GitHubCodeExamplesSource."""
        self.web_search_source = WebSearchSource()
    
    def _set_web_read_tool(self, web_read_tool):
        """Set the web_read tool to use for queries."""
        self.web_search_source._set_web_read_tool(web_read_tool)
    
    async def query(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query GitHub for code examples.
        
        Args:
            context: A dictionary containing query context information
                - query: The search query string
                - language: The programming language to search for
                - type: The type of information being sought (api_doc, error_solution, implementation)
                - max_results: Maximum number of results to return (default: 3)
                
        Returns:
            A list of dictionaries containing retrieved information
        """
        query = context.get("query", "")
        language = context.get("language", "")
        
        if not query:
            logger.warning("GitHubCodeExamplesSource: empty query")
            return []
        
        # Add site-specific search and language filter to the context
        search_context = context.copy()
        
        if language:
            search_context["query"] = f"site:github.com {query} language:{language} filename:{language}"
        else:
            search_context["query"] = f"site:github.com {query}"
        
        # Use the web search source to perform the query
        results = await self.web_search_source.query(search_context)
        
        # Process the results to extract code examples
        for result in results:
            # Add GitHub specific metadata
            result["platform"] = "GitHub"
            
            # Try to extract the repository name
            url = result.get("url", "")
            if "github.com" in url:
                parts = url.split("github.com/")
                if len(parts) > 1:
                    repo_path = parts[1].split("/")
                    if len(repo_path) >= 2:
                        result["repository"] = f"{repo_path[0]}/{repo_path[1]}"
        
        return results