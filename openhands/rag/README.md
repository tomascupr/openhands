# Code-Aware Retrieval-Augmented Generation (RAG)

This module provides a Code-Aware RAG system for OpenHands, enabling the agent to retrieve relevant code documentation, examples, and solutions based on the current coding context.

## Overview

Code-Aware RAG extends traditional RAG systems by specifically optimizing for software development contexts. While standard RAG systems retrieve general knowledge, Code-Aware RAG understands code semantics, project structure, and programming concepts to retrieve precisely relevant documentation, examples, and solutions that match the developer's current context and needs.

## Key Components

### Context Extraction

The `CodeContextExtractor` class analyzes code to extract relevant context, including:
- Import statements to identify libraries in use
- Function/method calls to identify APIs being used
- Error messages to extract error types and details
- Natural language queries to identify programming intent

### Query Building

The `CodeQueryBuilder` class constructs effective queries for different types of information:
- API usage examples
- Error solutions
- Implementation examples

### Source Adapters

The system includes adapters for retrieving information from various sources:
- `OfficialDocumentationSource`: Retrieves from official documentation sites
- `StackOverflowSource`: Retrieves relevant answers from Stack Overflow
- `GitHubCodeExamplesSource`: Retrieves code examples from GitHub repositories

### Result Ranking

The `CodeResultRanker` class ranks retrieved results based on relevance to the current context, considering factors like:
- Query type (API documentation, error solution, implementation)
- Library and function mentions
- Code examples
- Solution indicators
- Source credibility

## Usage

The Code-Aware RAG system is integrated with the CodeActAgent as a tool. When enabled, it provides the following capabilities:

1. **API Documentation Retrieval**: Find documentation and examples for specific API functions
2. **Error Solution Retrieval**: Find solutions for specific error messages
3. **Implementation Example Retrieval**: Find examples for implementing specific tasks

### Example

```python
# Retrieve API documentation
results = await code_rag_tool(
    query_type="api_doc",
    query="pandas.read_csv",
    library="pandas",
    function="read_csv"
)

# Retrieve error solutions
results = await code_rag_tool(
    query_type="error_solution",
    query="ZeroDivisionError: division by zero"
)

# Retrieve implementation examples
results = await code_rag_tool(
    query_type="implementation",
    query="web scraper to extract product prices",
    file_content=current_file_content,
    language="python"
)
```

## Configuration

To enable the Code-Aware RAG tool, set `enable_code_rag = true` in your agent configuration. Note that the tool requires the web browsing capability to be enabled as well (`enable_browsing = true`).

## Benefits

1. **Reduced Hallucination**: By grounding responses in actual documentation, the agent makes fewer incorrect API usage claims
2. **Expanded Knowledge**: The agent effectively has access to up-to-date documentation beyond its training cutoff
3. **Faster Problem Solving**: Instead of trial-and-error approaches, the agent can quickly find established solutions
4. **Better Error Recovery**: When errors occur, the agent can efficiently find and apply known solutions
5. **Improved Code Quality**: Access to best practices and idiomatic examples results in higher quality code generation