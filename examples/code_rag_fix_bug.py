"""
Example of using Code-Aware RAG to fix a bug in a Python script.
"""
import asyncio
import sys
import traceback
from pathlib import Path

from openhands.agenthub.codeact_agent.tools.code_rag import CodeRAGTool
from openhands.rag.context_extractor import CodeContextExtractor


async def main():
    """Run the example."""
    # Step 1: Run the buggy script and capture the error
    print("=== Running the buggy script ===")
    try:
        # Import and run the buggy script
        import examples.buggy_script
        examples.buggy_script.main()
    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)
        traceback_str = traceback.format_exc()
        print(f"\nError: {error_type}: {error_message}")
        print(f"\nTraceback:\n{traceback_str}")
    
    # Step 2: Read the buggy script file
    script_path = Path(__file__).parent / "buggy_script.py"
    with open(script_path, "r") as f:
        file_content = f.read()
    
    # Step 3: Create a simple web_read_tool function for our RAG system
    async def web_read_tool(url: str) -> str:
        print(f"Fetching: {url}")
        # This is a simplified implementation that returns hardcoded content
        # for the specific error we're dealing with
        if "TypeError" in url:
            return """
            <h1>TypeError in Python</h1>
            <p>TypeError is raised when an operation or function is applied to an object of inappropriate type.</p>
            <p>Common examples include:</p>
            <ul>
                <li>Trying to add a string and an integer without conversion</li>
                <li>Calling a method on an object that doesn't support it</li>
                <li>Passing an argument of the wrong type to a function</li>
            </ul>
            <h2>Example: String Concatenation Error</h2>
            <p>One common TypeError is when trying to concatenate a string with a non-string value:</p>
            <pre>
            # This will cause an error
            name = "Alice"
            age = 30
            message = "Hello, " + name + "! You are " + age + " years old."
            # TypeError: can only concatenate str (not "int") to str
            
            # Fix by converting the int to a string
            message = "Hello, " + name + "! You are " + str(age) + " years old."
            
            # Or better, use f-strings
            message = f"Hello, {name}! You are {age} years old."
            </pre>
            """
        else:
            return "<p>No specific content available for this URL.</p>"
    
    # Step 4: Create the CodeRAGTool
    rag_tool = CodeRAGTool(web_read_tool)
    
    # Step 5: Extract context from the buggy script
    print("\n=== Analyzing the code ===")
    extractor = CodeContextExtractor()
    imports = extractor.extract_imports(file_content)
    function_calls = extractor.extract_function_calls(file_content)
    
    print("\nDetected imports:")
    for imp in imports:
        print(f"  - {imp.get('original', '')}")
    
    print("\nDetected function calls:")
    for call in function_calls:
        if call["type"] == "method_call":
            print(f"  - {call['object']}.{call['method']}()")
        else:
            print(f"  - {call['function']}()")
    
    # Step 6: Get error solutions from the RAG system
    print("\n=== Getting solutions for the error ===")
    error_message = "TypeError: can only concatenate str (not \"int\") to str"
    error_results = await rag_tool.retrieve_error_solutions(error_message)
    
    print("\n" + rag_tool.format_results(error_results))
    
    # Step 7: Fix the bug and show the corrected code
    print("\n=== Fixing the bug ===")
    fixed_code = file_content.replace(
        'return "Hello, " + name + "! You are " + age + " years old."',
        'return f"Hello, {name}! You are {age} years old."'
    )
    
    print("\nFixed code:")
    print("```python")
    print(fixed_code)
    print("```")
    
    # Step 8: Save the fixed code to a new file
    fixed_path = Path(__file__).parent / "fixed_script.py"
    with open(fixed_path, "w") as f:
        f.write(fixed_code)
    
    print(f"\nFixed code saved to: {fixed_path}")
    
    # Step 9: Run the fixed script
    print("\n=== Running the fixed script ===")
    try:
        # Clear the module from sys.modules to reload it
        if "examples.buggy_script" in sys.modules:
            del sys.modules["examples.buggy_script"]
        
        # Import the module from the fixed file
        import importlib.util
        spec = importlib.util.spec_from_file_location("fixed_script", fixed_path)
        fixed_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixed_module)
        
        # Run the main function
        fixed_module.main()
        print("\nSuccess! The bug has been fixed.")
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())