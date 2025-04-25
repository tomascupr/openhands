"""
Web search adapter for retrieving code documentation and examples.
"""
import re
import urllib.parse
from typing import Dict, List, Any, Optional

from openhands.core.logger import openhands_logger as logger
from openhands.rag.sources.base import CodeDocumentationSource


class WebSearchSource(CodeDocumentationSource):
    """Retrieves information from web search results."""
    
    def __init__(self):
        """Initialize the WebSearchSource."""
        self.web_read_tool = None
    
    def _set_web_read_tool(self, web_read_tool):
        """Set the web_read tool to use for queries."""
        self.web_read_tool = web_read_tool
    
    async def query(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query web search with the given context.
        
        Args:
            context: A dictionary containing query context information
                - query: The search query string
                - type: The type of information being sought (api_doc, error_solution, implementation)
                - max_results: Maximum number of results to return (default: 3)
                
        Returns:
            A list of dictionaries containing retrieved information
        """
        if not self.web_read_tool:
            logger.warning("WebSearchSource: web_read_tool not set")
            return []
        
        query = context.get("query", "")
        if not query:
            logger.warning("WebSearchSource: empty query")
            return []
        
        query_type = context.get("type", "")
        max_results = context.get("max_results", 3)
        
        # Enhance the query based on the type
        enhanced_query = self._enhance_query(query, query_type)
        
        # Construct the search URL
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(enhanced_query)}"
        
        try:
            # Use the web_read tool to get search results
            search_results = await self.web_read_tool(url=search_url)
            
            # Parse the results
            parsed_results = self._parse_search_results(search_results, max_results)
            
            # If we have URLs, fetch the content of the top results
            detailed_results = []
            for result in parsed_results[:max_results]:
                if "url" in result:
                    try:
                        page_content = await self.web_read_tool(url=result["url"])
                        result["content"] = self._extract_relevant_content(
                            page_content, query, query_type
                        )
                        detailed_results.append(result)
                    except Exception as e:
                        logger.warning(f"Failed to fetch content from {result['url']}: {e}")
            
            return detailed_results
        except Exception as e:
            logger.warning(f"WebSearchSource query failed: {e}")
            return []
    
    def _enhance_query(self, query: str, query_type: str) -> str:
        """Enhance the query based on the type of information being sought."""
        if query_type == "api_doc":
            return f"{query} documentation example"
        elif query_type == "error_solution":
            return f"{query} solution fix"
        elif query_type == "implementation":
            return f"{query} code example tutorial"
        else:
            return query
    
    def _parse_search_results(self, search_results: str, max_results: int) -> List[Dict[str, Any]]:
        """Parse search results to extract URLs and titles."""
        results = []
        
        # This is a simplified parser for demonstration
        # A real implementation would need more robust parsing
        
        # Look for links in the search results
        link_pattern = r'<a href="(https?://[^"]+)"[^>]*>(.*?)</a>'
        for match in re.finditer(link_pattern, search_results):
            url = match.group(1)
            title = re.sub(r'<[^>]+>', '', match.group(2))  # Remove HTML tags
            
            # Skip Google's own links and other non-content links
            if "google.com" in url or "accounts.google" in url or "support.google" in url:
                continue
                
            results.append({
                "url": url,
                "title": title,
                "source": url,
                "content": None  # Will be filled in later
            })
            
            if len(results) >= max_results:
                break
        
        return results
    
    def _extract_relevant_content(self, page_content: str, query: str, query_type: str) -> str:
        """Extract the most relevant content from the page based on the query."""
        # This is a simplified extractor for demonstration
        # A real implementation would use more sophisticated techniques
        
        # Convert to plain text if it's HTML
        if "<html" in page_content.lower():
            # Very simple HTML to text conversion
            text = re.sub(r'<[^>]+>', ' ', page_content)
            text = re.sub(r'\s+', ' ', text).strip()
        else:
            text = page_content
        
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Score paragraphs based on query terms
        query_terms = set(query.lower().split())
        scored_paragraphs = []
        
        for para in paragraphs:
            if len(para.strip()) < 50:  # Skip very short paragraphs
                continue
                
            para_lower = para.lower()
            score = sum(1 for term in query_terms if term in para_lower)
            
            # Boost score for code blocks
            if '```' in para or 'def ' in para or 'function ' in para or 'class ' in para:
                score += 3
                
            # Boost score for relevant headings
            if query_type == "api_doc" and any(x in para_lower for x in ["example", "usage", "api", "function"]):
                score += 2
            elif query_type == "error_solution" and any(x in para_lower for x in ["error", "exception", "fix", "solution"]):
                score += 2
            elif query_type == "implementation" and any(x in para_lower for x in ["implementation", "example", "tutorial", "guide"]):
                score += 2
                
            scored_paragraphs.append((score, para))
        
        # Sort by score and take top paragraphs
        scored_paragraphs.sort(reverse=True)
        top_paragraphs = [para for _, para in scored_paragraphs[:5]]
        
        # Join the top paragraphs
        return "\n\n".join(top_paragraphs)