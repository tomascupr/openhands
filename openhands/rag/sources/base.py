"""
Base classes for documentation sources.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class CodeDocumentationSource(ABC):
    """Base class for documentation sources."""
    
    @abstractmethod
    async def query(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query the source with the given context.
        
        Args:
            context: A dictionary containing query context information
            
        Returns:
            A list of dictionaries containing retrieved information
        """
        raise NotImplementedError()
    
    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format the results for display.
        
        Args:
            results: A list of dictionaries containing retrieved information
            
        Returns:
            A formatted string representation of the results
        """
        if not results:
            return "No results found."
        
        formatted = []
        for i, result in enumerate(results, 1):
            title = result.get("title", f"Result {i}")
            content = result.get("content", "No content available.")
            source = result.get("source", "Unknown source")
            
            formatted.append(f"### {title}\n\n{content}\n\nSource: {source}\n")
        
        return "\n".join(formatted)