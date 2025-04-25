"""
Tool for retrieving relevant code documentation and examples.
"""
import asyncio
from typing import Dict, List, Any, Optional, Callable

from openhands.agenthub.codeact_agent.tools.web_read import WebReadTool
from openhands.core.logger import openhands_logger as logger
from openhands.rag.context_extractor import CodeContextExtractor
from openhands.rag.query_builder import CodeQueryBuilder
from openhands.rag.ranker import CodeResultRanker
from openhands.rag.sources.base import CodeDocumentationSource
from openhands.rag.sources.official_docs import OfficialDocumentationSource
from openhands.rag.sources.stackoverflow import StackOverflowSource
from openhands.rag.sources.github import GitHubCodeExamplesSource


class CodeRAGTool:
    """Tool for retrieving relevant code documentation and examples."""
    
    def __init__(self, web_read_tool: Optional[WebReadTool] = None):
        """
        Initialize the CodeRAGTool.
        
        Args:
            web_read_tool: The web_read tool to use for queries
        """
        self.context_extractor = CodeContextExtractor()
        self.query_builder = CodeQueryBuilder()
        self.ranker = CodeResultRanker()
        
        # Initialize sources
        self.sources = [
            OfficialDocumentationSource(),
            StackOverflowSource(),
            GitHubCodeExamplesSource(),
        ]
        
        # Set the web_read tool for all sources
        if web_read_tool:
            self.set_web_read_tool(web_read_tool)
        
        # Simple in-memory cache
        self.cache = {}
    
    def set_web_read_tool(self, web_read_tool: Callable):
        """
        Set the web_read tool to use for queries.
        
        Args:
            web_read_tool: The web_read tool function
        """
        for source in self.sources:
            source._set_web_read_tool(web_read_tool)
    
    async def retrieve_api_documentation(
        self, 
        library: str, 
        function: str, 
        context: str = "",
        max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documentation for a specific API function.
        
        Args:
            library: The library or module name
            function: The function or method name
            context: Additional context for the query
            max_results: Maximum number of results to return
            
        Returns:
            A list of dictionaries containing retrieved information
        """
        cache_key = f"api_doc:{library}:{function}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        query = self.query_builder.build_api_usage_query(library, function, context)
        
        query_context = {
            "query": query,
            "type": "api_doc",
            "library": library,
            "function": function,
            "max_results": max_results
        }
        
        results = await self._query_sources(query_context)
        
        ranked_results = self.ranker.rank_results(
            results, 
            {"type": "api_doc", "library": library, "function": function}
        )
        
        # Cache the results
        self.cache[cache_key] = ranked_results
        
        return ranked_results
    
    async def retrieve_error_solutions(
        self, 
        error_message: str,
        max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve solutions for a specific error message.
        
        Args:
            error_message: The error message to find solutions for
            max_results: Maximum number of results to return
            
        Returns:
            A list of dictionaries containing retrieved information
        """
        # Extract error context
        error_context = self.context_extractor.extract_error_context(error_message)
        
        # Build the query
        query = self.query_builder.build_error_resolution_query(
            error_context.get("error_type", ""), 
            error_context.get("error_message", "")
        )
        
        query_context = {
            "query": query,
            "type": "error_solution",
            "error_type": error_context.get("error_type", ""),
            "error_message": error_context.get("error_message", ""),
            "max_results": max_results
        }
        
        results = await self._query_sources(query_context)
        
        ranked_results = self.ranker.rank_results(results, error_context)
        
        return ranked_results
    
    async def retrieve_implementation_examples(
        self, 
        task_description: str, 
        file_content: str = "", 
        language: str = "python",
        max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve implementation examples for a described task.
        
        Args:
            task_description: Description of the task to implement
            file_content: Content of the current file for context extraction
            language: The programming language
            max_results: Maximum number of results to return
            
        Returns:
            A list of dictionaries containing retrieved information
        """
        # Extract libraries from the file content
        imports = self.context_extractor.extract_imports(file_content, language)
        libraries = [imp.get("module") for imp in imports if imp.get("type") == "import"]
        
        # Build the query
        query = self.query_builder.build_implementation_query(task_description, libraries)
        
        query_context = {
            "query": query,
            "type": "implementation",
            "language": language,
            "max_results": max_results
        }
        
        results = await self._query_sources(query_context)
        
        ranked_results = self.ranker.rank_results(
            results, 
            {"type": "implementation", "task": task_description, "libraries": libraries}
        )
        
        return ranked_results
    
    async def _query_sources(self, query_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query all sources and combine results."""
        all_results = []
        
        # Query each source concurrently
        tasks = [source.query(query_context) for source in self.sources]
        source_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results, handling any exceptions
        for i, result in enumerate(source_results):
            if isinstance(result, Exception):
                logger.warning(f"Error querying source {self.sources[i].__class__.__name__}: {result}")
            else:
                all_results.extend(result)
        
        return all_results
    
    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format the results for display.
        
        Args:
            results: A list of dictionaries containing retrieved information
            
        Returns:
            A formatted string representation of the results
        """
        if not results:
            return "No relevant information found."
        
        formatted = []
        
        for i, result in enumerate(results, 1):
            title = result.get("title", f"Result {i}")
            content = result.get("content", "No content available.")
            source = result.get("source", "Unknown source")
            platform = result.get("platform", "")
            
            # Format the result
            result_str = f"### {title}\n\n"
            
            # Add platform-specific information
            if platform == "Stack Overflow":
                votes = result.get("votes", 0)
                result_str += f"**Source**: Stack Overflow ({votes} votes)\n\n"
            elif platform == "GitHub":
                repo = result.get("repository", "")
                if repo:
                    result_str += f"**Source**: GitHub - {repo}\n\n"
                else:
                    result_str += f"**Source**: GitHub\n\n"
            else:
                result_str += f"**Source**: {source}\n\n"
            
            # Add the content
            result_str += f"{content}\n\n"
            
            formatted.append(result_str)
        
        return "\n".join(formatted)


def create_code_rag_tool(web_read_tool):
    """
    Create a CodeRAGTool instance with the given web_read_tool.
    
    Args:
        web_read_tool: The web_read tool function
        
    Returns:
        A dictionary describing the tool
    """
    async def code_rag_tool(
        query_type: str,
        query: str,
        library: str = "",
        function: str = "",
        file_content: str = "",
        language: str = "python",
        max_results: int = 3
    ):
        """
        Retrieve relevant code documentation and examples.
        
        Args:
            query_type: Type of query ("api_doc", "error_solution", "implementation")
            query: The query string (API function, error message, or task description)
            library: The library or module name (for API documentation)
            function: The function or method name (for API documentation)
            file_content: Content of the current file for context extraction
            language: The programming language
            max_results: Maximum number of results to return
            
        Returns:
            A formatted string containing the retrieved information
        """
        rag_tool = CodeRAGTool(web_read_tool)
        
        if query_type == "api_doc":
            results = await rag_tool.retrieve_api_documentation(
                library or query.split('.')[0],
                function or query.split('.')[-1],
                "",
                max_results
            )
        elif query_type == "error_solution":
            results = await rag_tool.retrieve_error_solutions(query, max_results)
        elif query_type == "implementation":
            results = await rag_tool.retrieve_implementation_examples(
                query, file_content, language, max_results
            )
        else:
            return f"Invalid query_type: {query_type}. Must be one of: api_doc, error_solution, implementation."
        
        return rag_tool.format_results(results)
    
    return {
        "name": "code_rag",
        "description": "Retrieve relevant code documentation, examples, and solutions.",
        "parameters": {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "enum": ["api_doc", "error_solution", "implementation"],
                    "description": "Type of query to perform"
                },
                "query": {
                    "type": "string",
                    "description": "The query string (API function, error message, or task description)"
                },
                "library": {
                    "type": "string",
                    "description": "The library or module name (for API documentation)"
                },
                "function": {
                    "type": "string",
                    "description": "The function or method name (for API documentation)"
                },
                "file_content": {
                    "type": "string",
                    "description": "Content of the current file for context extraction"
                },
                "language": {
                    "type": "string",
                    "description": "The programming language"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return"
                }
            },
            "required": ["query_type", "query"]
        },
        "function": code_rag_tool
    }