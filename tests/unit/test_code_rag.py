"""
Tests for the Code-Aware RAG system.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from openhands.rag.context_extractor import CodeContextExtractor
from openhands.rag.query_builder import CodeQueryBuilder
from openhands.rag.ranker import CodeResultRanker
from openhands.rag.sources.web_search import WebSearchSource
from openhands.rag.sources.official_docs import OfficialDocumentationSource
from openhands.rag.sources.stackoverflow import StackOverflowSource
from openhands.rag.sources.github import GitHubCodeExamplesSource
from openhands.agenthub.codeact_agent.tools.code_rag import CodeRAGTool


class TestCodeContextExtractor:
    """Tests for the CodeContextExtractor class."""
    
    def test_extract_python_imports_regex(self):
        """Test extracting Python imports using regex."""
        extractor = CodeContextExtractor()
        
        # Test simple import
        code = "import numpy as np\nimport pandas"
        imports = extractor._extract_python_imports_regex(code)
        
        assert len(imports) == 2
        assert imports[0]["type"] == "import"
        assert imports[0]["module"] == "numpy"
        assert imports[0]["alias"] == "np"
        assert imports[1]["type"] == "import"
        assert imports[1]["module"] == "pandas"
        assert imports[1]["alias"] is None
        
        # Test from import
        code = "from os import path\nfrom sys import argv, exit"
        imports = extractor._extract_python_imports_regex(code)
        
        assert len(imports) == 2
        assert imports[0]["type"] == "from_import"
        assert imports[0]["module"] == "os"
        assert len(imports[0]["imports"]) == 1
        assert imports[0]["imports"][0]["name"] == "path"
        
        assert imports[1]["type"] == "from_import"
        assert imports[1]["module"] == "sys"
        assert len(imports[1]["imports"]) == 2
        assert imports[1]["imports"][0]["name"] == "argv"
        assert imports[1]["imports"][1]["name"] == "exit"
    
    def test_extract_function_calls(self):
        """Test extracting function calls."""
        extractor = CodeContextExtractor()
        
        code = "result = np.array([1, 2, 3])\ndf = pd.DataFrame(data)\nprint('hello')"
        calls = extractor.extract_function_calls(code)
        
        assert len(calls) >= 3
        
        # Check for method calls
        method_calls = [call for call in calls if call["type"] == "method_call"]
        assert any(call["full_name"] == "np.array" for call in method_calls)
        assert any(call["full_name"] == "pd.DataFrame" for call in method_calls)
        
        # Check for function calls
        function_calls = [call for call in calls if call["type"] == "function_call"]
        assert any(call["function"] == "print" for call in function_calls)
    
    def test_extract_error_context(self):
        """Test extracting error context."""
        extractor = CodeContextExtractor()
        
        error_message = """Traceback (most recent call last):
  File "test.py", line 10, in <module>
    result = divide(10, 0)
  File "test.py", line 5, in divide
    return a / b
ZeroDivisionError: division by zero"""
        
        error_info = extractor.extract_error_context(error_message)
        
        assert error_info["error_type"] == "ZeroDivisionError"
        assert error_info["error_message"] == "division by zero"
        assert error_info["file_path"] == "test.py"
        # The regex is matching the first occurrence of line number, which is 10
        assert error_info["line_number"] == "10"


class TestCodeQueryBuilder:
    """Tests for the CodeQueryBuilder class."""
    
    def test_build_api_usage_query(self):
        """Test building API usage queries."""
        builder = CodeQueryBuilder()
        
        query = builder.build_api_usage_query("pandas", "read_csv")
        assert "pandas" in query
        assert "read_csv" in query
        assert "example" in query
        
        query = builder.build_api_usage_query("numpy", "array", "3d matrix")
        assert "numpy" in query
        assert "array" in query
        assert "3d matrix" in query
    
    def test_build_error_resolution_query(self):
        """Test building error resolution queries."""
        builder = CodeQueryBuilder()
        
        query = builder.build_error_resolution_query("ZeroDivisionError", "division by zero")
        assert "ZeroDivisionError" in query
        assert "division by zero" in query
    
    def test_build_implementation_query(self):
        """Test building implementation queries."""
        builder = CodeQueryBuilder()
        
        query = builder.build_implementation_query("web scraper", ["requests", "beautifulsoup"])
        assert "web scraper" in query
        assert "requests" in query
        assert "beautifulsoup" in query
        assert "code example implementation" in query


class TestCodeResultRanker:
    """Tests for the CodeResultRanker class."""
    
    def test_rank_results(self):
        """Test ranking results."""
        ranker = CodeResultRanker()
        
        results = [
            {
                "title": "Official pandas documentation",
                "content": "pandas.read_csv is a function to read CSV files",
                "url": "https://pandas.pydata.org/docs/",
                "source": "pandas.pydata.org"
            },
            {
                "title": "How to read CSV files in Python",
                "content": "```python\nimport pandas as pd\ndf = pd.read_csv('file.csv')\n```",
                "url": "https://stackoverflow.com/questions/12345",
                "source": "stackoverflow.com",
                "platform": "Stack Overflow",
                "votes": 50
            },
            {
                "title": "Python data analysis",
                "content": "Data analysis can be done with various libraries",
                "url": "https://example.com/blog",
                "source": "example.com"
            }
        ]
        
        context = {
            "type": "api_doc",
            "library": "pandas",
            "function": "read_csv"
        }
        
        ranked = ranker.rank_results(results, context)
        
        # The Stack Overflow result with code example should be ranked higher
        assert ranked[0]["url"] == "https://stackoverflow.com/questions/12345"


@pytest.mark.asyncio
class TestCodeRAGTool:
    """Tests for the CodeRAGTool class."""
    
    async def test_retrieve_api_documentation(self):
        """Test retrieving API documentation."""
        # Create a mock web_read_tool
        mock_web_read = AsyncMock()
        mock_web_read.return_value = """
        <html>
            <body>
                <h1>pandas.read_csv</h1>
                <p>Read a comma-separated values (csv) file into DataFrame.</p>
                <pre>
                import pandas as pd
                df = pd.read_csv('file.csv')
                </pre>
            </body>
        </html>
        """
        
        # Create the CodeRAGTool with the mock
        rag_tool = CodeRAGTool(mock_web_read)
        
        # Mock the _query_sources method to return test results
        rag_tool._query_sources = AsyncMock()
        rag_tool._query_sources.return_value = [
            {
                "title": "pandas.read_csv documentation",
                "content": "Read a comma-separated values (csv) file into DataFrame.",
                "url": "https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html",
                "source": "pandas.pydata.org"
            }
        ]
        
        results = await rag_tool.retrieve_api_documentation("pandas", "read_csv")
        
        assert len(results) == 1
        assert "pandas" in results[0]["title"]
        assert "read_csv" in results[0]["title"]
        
        # Verify the query was constructed correctly
        query_context = rag_tool._query_sources.call_args[0][0]
        assert query_context["type"] == "api_doc"
        assert query_context["library"] == "pandas"
        assert query_context["function"] == "read_csv"
    
    async def test_retrieve_error_solutions(self):
        """Test retrieving error solutions."""
        # Create a mock web_read_tool
        mock_web_read = AsyncMock()
        
        # Create the CodeRAGTool with the mock
        rag_tool = CodeRAGTool(mock_web_read)
        
        # Mock the _query_sources method to return test results
        rag_tool._query_sources = AsyncMock()
        rag_tool._query_sources.return_value = [
            {
                "title": "How to fix ZeroDivisionError in Python",
                "content": "You need to check if the denominator is zero before division.",
                "url": "https://stackoverflow.com/questions/12345",
                "source": "stackoverflow.com",
                "platform": "Stack Overflow",
                "votes": 50
            }
        ]
        
        error_message = "ZeroDivisionError: division by zero"
        results = await rag_tool.retrieve_error_solutions(error_message)
        
        assert len(results) == 1
        assert "ZeroDivisionError" in results[0]["title"]
        
        # Verify the query was constructed correctly
        query_context = rag_tool._query_sources.call_args[0][0]
        assert query_context["type"] == "error_solution"
        assert "ZeroDivisionError" in query_context["query"]
    
    async def test_retrieve_implementation_examples(self):
        """Test retrieving implementation examples."""
        # Create a mock web_read_tool
        mock_web_read = AsyncMock()
        
        # Create the CodeRAGTool with the mock
        rag_tool = CodeRAGTool(mock_web_read)
        
        # Mock the _query_sources method to return test results
        rag_tool._query_sources = AsyncMock()
        rag_tool._query_sources.return_value = [
            {
                "title": "Web scraper example with Python",
                "content": "```python\nimport requests\nfrom bs4 import BeautifulSoup\n\nurl = 'https://example.com'\nresponse = requests.get(url)\nsoup = BeautifulSoup(response.text, 'html.parser')\n```",
                "url": "https://github.com/user/repo",
                "source": "github.com",
                "platform": "GitHub",
                "repository": "user/repo"
            }
        ]
        
        file_content = "import requests\nimport bs4"
        results = await rag_tool.retrieve_implementation_examples("web scraper", file_content)
        
        assert len(results) == 1
        assert "Web scraper" in results[0]["title"]
        
        # Verify the query was constructed correctly
        query_context = rag_tool._query_sources.call_args[0][0]
        assert query_context["type"] == "implementation"
        assert "web scraper" in query_context["query"]