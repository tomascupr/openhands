"""
Stack Overflow source adapter.
"""
import re
from typing import Dict, List, Any

from openhands.core.logger import openhands_logger as logger
from openhands.rag.sources.base import CodeDocumentationSource
from openhands.rag.sources.web_search import WebSearchSource


class StackOverflowSource(CodeDocumentationSource):
    """Retrieves relevant answers from Stack Overflow."""
    
    def __init__(self):
        """Initialize the StackOverflowSource."""
        self.web_search_source = WebSearchSource()
    
    def _set_web_read_tool(self, web_read_tool):
        """Set the web_read tool to use for queries."""
        self.web_search_source._set_web_read_tool(web_read_tool)
    
    async def query(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query Stack Overflow for relevant answers.
        
        Args:
            context: A dictionary containing query context information
                - query: The search query string
                - type: The type of information being sought (api_doc, error_solution, implementation)
                - max_results: Maximum number of results to return (default: 3)
                
        Returns:
            A list of dictionaries containing retrieved information
        """
        query = context.get("query", "")
        if not query:
            logger.warning("StackOverflowSource: empty query")
            return []
        
        # Add site-specific search to the context
        search_context = context.copy()
        search_context["query"] = f"site:stackoverflow.com {query}"
        
        # Use the web search source to perform the query
        results = await self.web_search_source.query(search_context)
        
        # Process the results to extract answers
        for result in results:
            # Add Stack Overflow specific metadata
            result["platform"] = "Stack Overflow"
            
            # Extract vote count if available
            content = result.get("content", "")
            vote_match = re.search(r'(\d+)\s+votes', content)
            if vote_match:
                result["votes"] = int(vote_match.group(1))
            else:
                result["votes"] = 0
        
        # Sort by votes if available
        results.sort(key=lambda x: x.get("votes", 0), reverse=True)
        
        return results