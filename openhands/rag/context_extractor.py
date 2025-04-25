"""
Module for extracting relevant context from the current coding environment.
"""
import re
from typing import Dict, List, Optional, Tuple

from tree_sitter import Language, Parser

from openhands.core.logger import openhands_logger as logger


class CodeContextExtractor:
    """Extracts relevant context from the current coding environment."""

    def __init__(self):
        """Initialize the CodeContextExtractor."""
        self.parser = None
        try:
            # Initialize tree-sitter parser
            # Note: This requires the language grammar to be built
            # We'll use regex-based fallbacks if tree-sitter isn't available
            self._setup_tree_sitter()
        except Exception as e:
            logger.warning(f"Tree-sitter initialization failed: {e}. Using regex fallbacks.")

    def _setup_tree_sitter(self):
        """Set up the tree-sitter parser."""
        try:
            from tree_sitter import Language, Parser
            
            # Check if Python language is available
            # In a full implementation, we would build/load language definitions
            # for multiple languages
            self.parser = Parser()
            # This path might need adjustment based on where language definitions are stored
            PY_LANGUAGE = Language('/workspace/openhands/build/py-tree-sitter.so', 'python')
            self.parser.set_language(PY_LANGUAGE)
        except Exception as e:
            logger.warning(f"Failed to set up tree-sitter: {e}")
            self.parser = None

    def extract_imports(self, file_content: str, language: str = "python") -> List[Dict[str, str]]:
        """
        Extract import statements from code to identify libraries in use.
        
        Args:
            file_content: The content of the file to analyze
            language: The programming language of the file
            
        Returns:
            A list of dictionaries containing import information
        """
        imports = []
        
        if language.lower() == "python":
            if self.parser:
                # Try using tree-sitter for more accurate parsing
                try:
                    tree = self.parser.parse(bytes(file_content, "utf8"))
                    import_nodes = self._find_import_nodes(tree.root_node)
                    
                    for node in import_nodes:
                        import_info = self._extract_python_import_info(node, file_content)
                        if import_info:
                            imports.append(import_info)
                except Exception as e:
                    logger.warning(f"Tree-sitter parsing failed: {e}. Falling back to regex.")
                    imports = self._extract_python_imports_regex(file_content)
            else:
                # Fallback to regex-based extraction
                imports = self._extract_python_imports_regex(file_content)
        elif language.lower() == "javascript" or language.lower() == "typescript":
            # Regex-based extraction for JS/TS
            imports = self._extract_js_imports_regex(file_content)
        
        return imports
    
    def _find_import_nodes(self, root_node):
        """Find all import nodes in the AST."""
        import_nodes = []
        
        def visit(node):
            if node.type == "import_statement" or node.type == "import_from_statement":
                import_nodes.append(node)
            
            for child in node.children:
                visit(child)
        
        visit(root_node)
        return import_nodes
    
    def _extract_python_import_info(self, node, file_content: str) -> Optional[Dict[str, str]]:
        """Extract import information from a tree-sitter node."""
        try:
            node_text = file_content[node.start_byte:node.end_byte]
            
            if node.type == "import_statement":
                # Handle "import x" or "import x as y"
                match = re.search(r'import\s+([^\s,]+)(?:\s+as\s+([^\s,]+))?', node_text)
                if match:
                    module = match.group(1)
                    alias = match.group(2) if match.group(2) else None
                    return {
                        "type": "import",
                        "module": module,
                        "alias": alias,
                        "original": node_text.strip()
                    }
            elif node.type == "import_from_statement":
                # Handle "from x import y" or "from x import y as z"
                from_match = re.search(r'from\s+([^\s]+)\s+import', node_text)
                if from_match:
                    module = from_match.group(1)
                    imports = []
                    
                    # Extract what's being imported
                    import_match = re.search(r'import\s+(.+)$', node_text)
                    if import_match:
                        imports_text = import_match.group(1)
                        
                        # Handle multiple imports separated by commas
                        for item in imports_text.split(','):
                            item = item.strip()
                            if item:
                                as_match = re.search(r'([^\s]+)(?:\s+as\s+([^\s]+))?', item)
                                if as_match:
                                    name = as_match.group(1)
                                    alias = as_match.group(2) if len(as_match.groups()) > 1 else None
                                    imports.append({"name": name, "alias": alias})
                    
                    return {
                        "type": "from_import",
                        "module": module,
                        "imports": imports,
                        "original": node_text.strip()
                    }
        except Exception as e:
            logger.warning(f"Failed to extract Python import info: {e}")
        
        return None
    
    def _extract_python_imports_regex(self, file_content: str) -> List[Dict[str, str]]:
        """Extract Python imports using regex."""
        imports = []
        
        # Match "import x" or "import x as y"
        import_pattern = r'^\s*import\s+([^\s,]+)(?:\s+as\s+([^\s,]+))?'
        for match in re.finditer(import_pattern, file_content, re.MULTILINE):
            module = match.group(1)
            alias = match.group(2) if len(match.groups()) > 1 else None
            imports.append({
                "type": "import",
                "module": module,
                "alias": alias,
                "original": match.group(0).strip()
            })
        
        # Match "from x import y" or "from x import y as z"
        from_import_pattern = r'^\s*from\s+([^\s]+)\s+import\s+(.+)$'
        for match in re.finditer(from_import_pattern, file_content, re.MULTILINE):
            module = match.group(1)
            imports_text = match.group(2)
            
            import_items = []
            for item in imports_text.split(','):
                item = item.strip()
                if item:
                    as_match = re.search(r'([^\s]+)(?:\s+as\s+([^\s]+))?', item)
                    if as_match:
                        name = as_match.group(1)
                        alias = as_match.group(2) if len(as_match.groups()) > 1 else None
                        import_items.append({"name": name, "alias": alias})
            
            imports.append({
                "type": "from_import",
                "module": module,
                "imports": import_items,
                "original": match.group(0).strip()
            })
        
        return imports
    
    def _extract_js_imports_regex(self, file_content: str) -> List[Dict[str, str]]:
        """Extract JavaScript/TypeScript imports using regex."""
        imports = []
        
        # Match "import { x } from 'y'" or "import x from 'y'"
        import_pattern = r'^\s*import\s+(?:{([^}]+)}|([^\s{]+))\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(import_pattern, file_content, re.MULTILINE):
            named_imports = match.group(1)
            default_import = match.group(2)
            module = match.group(3)
            
            if named_imports:
                import_items = []
                for item in named_imports.split(','):
                    item = item.strip()
                    if item:
                        as_match = re.search(r'([^\s]+)(?:\s+as\s+([^\s]+))?', item)
                        if as_match:
                            name = as_match.group(1)
                            alias = as_match.group(2) if len(as_match.groups()) > 1 else None
                            import_items.append({"name": name, "alias": alias})
                
                imports.append({
                    "type": "named_import",
                    "module": module,
                    "imports": import_items,
                    "original": match.group(0).strip()
                })
            
            if default_import:
                imports.append({
                    "type": "default_import",
                    "module": module,
                    "name": default_import,
                    "original": match.group(0).strip()
                })
        
        return imports

    def extract_function_calls(self, file_content: str, language: str = "python") -> List[Dict[str, str]]:
        """
        Extract function/method calls to identify APIs being used.
        
        Args:
            file_content: The content of the file to analyze
            language: The programming language of the file
            
        Returns:
            A list of dictionaries containing function call information
        """
        function_calls = []
        
        if language.lower() == "python":
            # Simple regex-based extraction for Python function calls
            # This is a simplified approach; a full implementation would use AST parsing
            
            # Match function calls like "func()" or "obj.method()"
            func_pattern = r'([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*)\s*\('
            for match in re.finditer(func_pattern, file_content):
                full_name = match.group(1)
                parts = full_name.split('.')
                
                if len(parts) > 1:
                    # It's a method call or namespaced function
                    obj = '.'.join(parts[:-1])
                    method = parts[-1]
                    function_calls.append({
                        "type": "method_call",
                        "object": obj,
                        "method": method,
                        "full_name": full_name
                    })
                else:
                    # It's a simple function call
                    function_calls.append({
                        "type": "function_call",
                        "function": full_name,
                        "full_name": full_name
                    })
        
        return function_calls

    def extract_error_context(self, error_message: str) -> Dict[str, str]:
        """
        Parse error messages to extract relevant context for retrieval.
        
        Args:
            error_message: The error message to parse
            
        Returns:
            A dictionary containing extracted error information
        """
        error_info = {
            "original_message": error_message,
            "error_type": None,
            "error_message": None,
            "file_path": None,
            "line_number": None,
        }
        
        # Try to extract Python error type and message
        python_error_match = re.search(r'([A-Za-z]+Error|Exception):\s*(.+?)(?:\n|$)', error_message)
        if python_error_match:
            error_info["error_type"] = python_error_match.group(1)
            error_info["error_message"] = python_error_match.group(2).strip()
        
        # Try to extract file path and line number
        file_line_match = re.search(r'File\s+"([^"]+)",\s+line\s+(\d+)', error_message)
        if file_line_match:
            error_info["file_path"] = file_line_match.group(1)
            error_info["line_number"] = file_line_match.group(2)
        
        # If we couldn't extract a specific error type, try to identify common patterns
        if not error_info["error_type"]:
            if "undefined" in error_message.lower() and "not defined" in error_message.lower():
                error_info["error_type"] = "NameError"
            elif "import" in error_message.lower() and "could not" in error_message.lower():
                error_info["error_type"] = "ImportError"
            elif "syntax" in error_message.lower():
                error_info["error_type"] = "SyntaxError"
        
        return error_info

    def extract_natural_language_intent(self, user_query: str) -> Dict[str, str]:
        """
        Extract programming intent from natural language queries.
        
        Args:
            user_query: The user's natural language query
            
        Returns:
            A dictionary containing extracted intent information
        """
        intent_info = {
            "original_query": user_query,
            "action": None,
            "language": None,
            "libraries": [],
            "task": user_query,
        }
        
        # Try to identify the programming language
        language_patterns = {
            "python": r'\b(?:python|py|pip|django|flask|pandas|numpy|tensorflow)\b',
            "javascript": r'\b(?:javascript|js|node|npm|react|vue|angular)\b',
            "typescript": r'\b(?:typescript|ts|tsx)\b',
            "java": r'\b(?:java|gradle|maven|spring)\b',
            "c#": r'\b(?:c#|\.net|asp\.net|csharp)\b',
            "ruby": r'\b(?:ruby|rails|gem)\b',
            "go": r'\b(?:go|golang)\b',
            "rust": r'\b(?:rust|cargo)\b',
            "php": r'\b(?:php|composer|laravel|symfony)\b',
        }
        
        for lang, pattern in language_patterns.items():
            if re.search(pattern, user_query, re.IGNORECASE):
                intent_info["language"] = lang
                break
        
        # Try to identify the action
        action_patterns = {
            "create": r'\b(?:create|make|build|implement|write)\b',
            "fix": r'\b(?:fix|solve|resolve|debug|correct)\b',
            "optimize": r'\b(?:optimize|improve|speed up|enhance)\b',
            "explain": r'\b(?:explain|understand|clarify|describe)\b',
            "test": r'\b(?:test|verify|validate|check)\b',
        }
        
        for action, pattern in action_patterns.items():
            if re.search(pattern, user_query, re.IGNORECASE):
                intent_info["action"] = action
                break
        
        # Try to identify mentioned libraries
        common_libraries = [
            "react", "vue", "angular", "django", "flask", "express", 
            "pandas", "numpy", "tensorflow", "pytorch", "scikit-learn",
            "requests", "axios", "jquery", "bootstrap", "tailwind",
            "spring", "hibernate", "laravel", "symfony", "rails"
        ]
        
        for lib in common_libraries:
            if re.search(r'\b' + re.escape(lib) + r'\b', user_query, re.IGNORECASE):
                intent_info["libraries"].append(lib)
        
        return intent_info