"""
Example script demonstrating the use of the Code-Aware RAG tool.
"""
import asyncio
import sys
from typing import Dict, List, Any

from openhands.agenthub.codeact_agent.tools.code_rag import CodeRAGTool
from openhands.rag.context_extractor import CodeContextExtractor


async def main():
    """Run the example."""
    # Create a simple web_read_tool function for demonstration
    # In a real scenario, this would be the actual web_read_tool from the agent
    async def mock_web_read_tool(url: str) -> str:
        print(f"Fetching: {url}")
        # This is a mock implementation that returns dummy content
        if "pandas" in url:
            return """
            <h1>pandas.read_csv</h1>
            <p>Read a comma-separated values (csv) file into DataFrame.</p>
            <pre>
            import pandas as pd
            df = pd.read_csv('file.csv')
            </pre>
            """
        elif "error" in url or "exception" in url:
            return """
            <h1>ZeroDivisionError in Python</h1>
            <p>This error occurs when you try to divide by zero.</p>
            <pre>
            try:
                result = x / y  # This will raise ZeroDivisionError if y is 0
            except ZeroDivisionError:
                print("Cannot divide by zero!")
            </pre>
            """
        else:
            return "<p>No specific content available for this URL.</p>"
    
    # Create the CodeRAGTool with our mock web_read_tool
    rag_tool = CodeRAGTool(mock_web_read_tool)
    
    # Example 1: API Documentation
    print("\n=== Example 1: API Documentation ===")
    api_results = await rag_tool.retrieve_api_documentation("pandas", "read_csv")
    print(rag_tool.format_results(api_results))
    
    # Example 2: Error Solutions
    print("\n=== Example 2: Error Solutions ===")
    error_message = "ZeroDivisionError: division by zero"
    error_results = await rag_tool.retrieve_error_solutions(error_message)
    print(rag_tool.format_results(error_results))
    
    # Example 3: Implementation Examples
    print("\n=== Example 3: Implementation Examples ===")
    file_content = """
    import requests
    from bs4 import BeautifulSoup
    
    # TODO: Implement web scraper
    """
    implementation_results = await rag_tool.retrieve_implementation_examples(
        "web scraper to extract product prices", file_content
    )
    print(rag_tool.format_results(implementation_results))
    
    # Example 4: Context Extraction
    print("\n=== Example 4: Context Extraction ===")
    extractor = CodeContextExtractor()
    
    code_sample = """
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split
    
    def process_data(df):
        # Clean the data
        df = df.dropna()
        
        # Normalize numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        df[numeric_cols] = (df[numeric_cols] - df[numeric_cols].mean()) / df[numeric_cols].std()
        
        return df
    
    # Load the data
    data = pd.read_csv('data.csv')
    processed_data = process_data(data)
    
    # Split into train and test sets
    X = processed_data.drop('target', axis=1)
    y = processed_data['target']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    """
    
    imports = extractor.extract_imports(code_sample)
    function_calls = extractor.extract_function_calls(code_sample)
    
    print("Detected imports:")
    for imp in imports:
        print(f"  - {imp['original']}")
    
    print("\nDetected function calls:")
    for call in function_calls:
        if call["type"] == "method_call":
            print(f"  - {call['object']}.{call['method']}()")
        else:
            print(f"  - {call['function']}()")


if __name__ == "__main__":
    asyncio.run(main())