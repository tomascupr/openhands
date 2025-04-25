"""
Official documentation source adapter.
"""
from typing import Dict, List, Any

from openhands.core.logger import openhands_logger as logger
from openhands.rag.sources.base import CodeDocumentationSource
from openhands.rag.sources.web_search import WebSearchSource


class OfficialDocumentationSource(CodeDocumentationSource):
    """Retrieves from official documentation sites."""
    
    def __init__(self):
        """Initialize the OfficialDocumentationSource."""
        self.web_search_source = WebSearchSource()
        self.doc_mappings = {
            "python": "https://docs.python.org/3/",
            "numpy": "https://numpy.org/doc/stable/",
            "pandas": "https://pandas.pydata.org/docs/",
            "tensorflow": "https://www.tensorflow.org/api_docs/python/",
            "pytorch": "https://pytorch.org/docs/stable/",
            "django": "https://docs.djangoproject.com/en/stable/",
            "flask": "https://flask.palletsprojects.com/en/latest/",
            "requests": "https://requests.readthedocs.io/en/latest/",
            "react": "https://react.dev/reference/",
            "vue": "https://vuejs.org/guide/",
            "angular": "https://angular.io/docs",
            "node": "https://nodejs.org/api/",
            "express": "https://expressjs.com/en/4x/api.html",
            "jquery": "https://api.jquery.com/",
            "java": "https://docs.oracle.com/en/java/javase/",
            "spring": "https://docs.spring.io/spring-framework/reference/",
            "go": "https://golang.org/doc/",
            "rust": "https://doc.rust-lang.org/std/",
        }
    
    def _set_web_read_tool(self, web_read_tool):
        """Set the web_read tool to use for queries."""
        self.web_search_source._set_web_read_tool(web_read_tool)
    
    async def query(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query official documentation with the given context.
        
        Args:
            context: A dictionary containing query context information
                - query: The search query string
                - library: The library to search documentation for
                - function: The specific function to look up (optional)
                - type: The type of information being sought (api_doc, error_solution, implementation)
                
        Returns:
            A list of dictionaries containing retrieved information
        """
        query = context.get("query", "")
        library = context.get("library", "")
        function = context.get("function", "")
        
        if not query and not (library and function):
            logger.warning("OfficialDocumentationSource: empty query and no library/function specified")
            return []
        
        # If we have a specific library and function, try to construct a direct URL
        if library and library.lower() in self.doc_mappings:
            base_url = self.doc_mappings[library.lower()]
            
            # Construct a more specific query with the library name
            if not query:
                query = f"{library} {function} documentation"
            else:
                query = f"{library} {query}"
            
            # Add site-specific search to the context
            search_context = context.copy()
            search_context["query"] = f"site:{base_url} {query}"
            
            return await self.web_search_source.query(search_context)
        
        # If we don't have a specific library mapping, fall back to general web search
        return await self.web_search_source.query(context)