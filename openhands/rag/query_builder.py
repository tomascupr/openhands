"""
Query builder for code documentation retrieval.
"""
from typing import Dict, List, Optional, Any


class CodeQueryBuilder:
    """Builds effective queries for code documentation retrieval."""
    
    def build_api_usage_query(self, library: str, function: str, context: str = "") -> str:
        """
        Build a query to find examples of specific API usage.
        
        Args:
            library: The library or module name
            function: The function or method name
            context: Additional context for the query
            
        Returns:
            A formatted query string
        """
        query = f"{library} {function} example"
        
        if context:
            # Add relevant context terms
            query += f" {context}"
        
        return query
    
    def build_error_resolution_query(self, error_type: str, error_message: str) -> str:
        """
        Build a query to find solutions for specific errors.
        
        Args:
            error_type: The type of error (e.g., "TypeError", "ImportError")
            error_message: The error message
            
        Returns:
            A formatted query string
        """
        # Clean the error message
        cleaned_message = error_message.replace('"', '').replace("'", "")
        
        # Truncate if too long
        if len(cleaned_message) > 100:
            cleaned_message = cleaned_message[:100]
        
        if error_type:
            return f"{error_type}: {cleaned_message}"
        else:
            return cleaned_message
    
    def build_implementation_query(self, task_description: str, libraries: List[str] = None) -> str:
        """
        Build a query to find implementation examples for a described task.
        
        Args:
            task_description: Description of the task to implement
            libraries: List of preferred libraries to use
            
        Returns:
            A formatted query string
        """
        query = task_description
        
        # Add library preferences if specified
        if libraries and len(libraries) > 0:
            lib_str = " ".join(libraries[:3])  # Limit to top 3 libraries
            query += f" using {lib_str}"
        
        # Add terms to find code examples
        query += " code example implementation"
        
        return query