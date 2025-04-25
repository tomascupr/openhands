"""
Result ranker for code documentation retrieval.
"""
import re
from typing import Dict, List, Any


class CodeResultRanker:
    """Ranks retrieved results based on relevance to the coding context."""
    
    def rank_results(self, results: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank results based on relevance to the current context.
        
        Args:
            results: List of retrieved results
            context: Dictionary containing context information
            
        Returns:
            Ranked list of results
        """
        if not results:
            return []
        
        # Extract context information
        query_type = context.get("type", "")
        library = context.get("library", "")
        function = context.get("function", "")
        error_type = context.get("error_type", "")
        
        # Score each result
        scored_results = []
        for result in results:
            score = self._calculate_score(result, query_type, library, function, error_type)
            scored_results.append((score, result))
        
        # Sort by score (descending)
        scored_results.sort(reverse=True)
        
        # Return the sorted results
        return [result for _, result in scored_results]
    
    def _calculate_score(
        self, 
        result: Dict[str, Any], 
        query_type: str, 
        library: str, 
        function: str, 
        error_type: str
    ) -> float:
        """Calculate a relevance score for a result."""
        score = 1.0  # Base score
        
        title = result.get("title", "").lower()
        content = result.get("content", "").lower()
        url = result.get("url", "").lower()
        
        # Check if content is available
        if not content:
            score -= 0.5
        
        # Score based on query type
        if query_type == "api_doc":
            # Prefer official documentation
            if "docs." in url or "documentation" in url:
                score += 1.0
            
            # Check for library and function mentions
            if library and library.lower() in title:
                score += 0.5
            if library and library.lower() in content:
                score += 0.3
            
            if function and function.lower() in title:
                score += 0.7
            if function and function.lower() in content:
                score += 0.4
            
            # Check for code examples
            if "example" in title or "usage" in title:
                score += 0.5
            if "example" in content or "usage" in content:
                score += 0.3
            
            # Check for code blocks
            if "```" in content or "<code>" in content:
                score += 0.8
            elif "def " in content or "function " in content or "class " in content:
                score += 0.5
        
        elif query_type == "error_solution":
            # Prefer Stack Overflow for error solutions
            if "stackoverflow.com" in url:
                score += 0.8
            
            # Check for error type mentions
            if error_type and error_type.lower() in title:
                score += 1.0
            if error_type and error_type.lower() in content:
                score += 0.6
            
            # Check for solution indicators
            if "solution" in title or "fix" in title or "solved" in title:
                score += 0.7
            if "solution" in content or "fix" in content or "solved" in content:
                score += 0.4
            
            # Check for code blocks that might contain solutions
            if "```" in content or "<code>" in content:
                score += 0.6
        
        elif query_type == "implementation":
            # Prefer GitHub for implementations
            if "github.com" in url:
                score += 0.7
            
            # Check for implementation indicators
            if "implementation" in title or "example" in title or "tutorial" in title:
                score += 0.8
            if "implementation" in content or "example" in content or "tutorial" in content:
                score += 0.5
            
            # Check for code blocks
            if "```" in content or "<code>" in content:
                score += 1.0
            elif "def " in content or "function " in content or "class " in content:
                score += 0.7
        
        # Adjust score based on result source
        platform = result.get("platform", "")
        if platform == "Stack Overflow":
            # Boost based on votes if available
            votes = result.get("votes", 0)
            if votes > 100:
                score += 0.8
            elif votes > 50:
                score += 0.5
            elif votes > 10:
                score += 0.3
        
        return score
    
    def filter_outdated_results(self, results: List[Dict[str, Any]], libraries: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Filter out results that reference outdated API versions.
        
        Args:
            results: List of retrieved results
            libraries: Dictionary mapping library names to their current versions
            
        Returns:
            Filtered list of results
        """
        if not libraries:
            return results
        
        filtered_results = []
        
        for result in results:
            content = result.get("content", "")
            
            # Check if the result mentions specific versions
            is_outdated = False
            
            for lib, current_version in libraries.items():
                # Look for version patterns like "library 1.2.3" or "library v1.2.3"
                version_pattern = rf"{re.escape(lib)}\s+(?:v|version\s+)?(\d+\.\d+(?:\.\d+)?)"
                matches = re.finditer(version_pattern, content, re.IGNORECASE)
                
                for match in matches:
                    mentioned_version = match.group(1)
                    
                    # Simple version comparison (this could be more sophisticated)
                    if self._is_version_outdated(mentioned_version, current_version):
                        is_outdated = True
                        break
            
            if not is_outdated:
                filtered_results.append(result)
        
        return filtered_results
    
    def _is_version_outdated(self, mentioned_version: str, current_version: str) -> bool:
        """
        Check if a mentioned version is significantly outdated compared to the current version.
        
        This is a simplified version comparison that just checks major and minor versions.
        A more sophisticated implementation would use proper semantic versioning comparison.
        """
        try:
            mentioned_parts = [int(p) for p in mentioned_version.split(".")]
            current_parts = [int(p) for p in current_version.split(".")]
            
            # Pad with zeros if needed
            while len(mentioned_parts) < 3:
                mentioned_parts.append(0)
            while len(current_parts) < 3:
                current_parts.append(0)
            
            # Check major version
            if mentioned_parts[0] < current_parts[0] - 1:
                return True
            
            # If same major version, check minor version
            if mentioned_parts[0] == current_parts[0] and mentioned_parts[1] < current_parts[1] - 3:
                return True
            
            return False
        except (ValueError, IndexError):
            # If we can't parse the versions, assume it's not outdated
            return False