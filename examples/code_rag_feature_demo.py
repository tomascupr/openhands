"""
Simplified demo of using Code-Aware RAG to implement a new feature.
"""
import asyncio
import os
from pathlib import Path

from openhands.agenthub.codeact_agent.tools.code_rag import CodeRAGTool
from openhands.rag.context_extractor import CodeContextExtractor


async def main():
    """Run the example."""
    # Step 1: Define the feature we want to implement
    feature_description = "web scraper to extract product prices from an e-commerce website"
    
    # Step 2: Create a starter file with imports
    starter_code = """
import requests
from bs4 import BeautifulSoup

# TODO: Implement a web scraper to extract product prices from an e-commerce website
"""
    
    starter_path = Path(__file__).parent / "starter_scraper.py"
    with open(starter_path, "w") as f:
        f.write(starter_code)
    
    print(f"=== Feature Request ===\nImplement a {feature_description}")
    print(f"\nStarter code created at: {starter_path}")
    print(f"Content:\n{starter_code}")
    
    # Step 3: Create a simple web_read_tool function for our RAG system
    async def web_read_tool(url: str) -> str:
        print(f"Fetching: {url}")
        # This is a simplified implementation that returns hardcoded content
        if "web-scraper" in url or "beautifulsoup" in url:
            return """
            <h1>Web Scraping with BeautifulSoup</h1>
            <p>BeautifulSoup is a Python library for parsing HTML and XML documents.</p>
            <h2>Basic Example</h2>
            <pre>
            import requests
            from bs4 import BeautifulSoup
            
            # Send a GET request to the URL
            url = "https://example.com"
            response = requests.get(url)
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find elements by tag
            all_paragraphs = soup.find_all('p')
            
            # Find elements by class
            products = soup.find_all(class_='product')
            
            # Find elements by ID
            header = soup.find(id='header')
            
            # Find elements by CSS selector
            items = soup.select('.item-container .price')
            </pre>
            
            <h2>E-commerce Scraper Example</h2>
            <pre>
            import requests
            from bs4 import BeautifulSoup
            
            def scrape_products(url):
                # Add headers to mimic a browser request
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                
                response = requests.get(url, headers=headers)
                
                # Check if the request was successful
                if response.status_code != 200:
                    print(f"Failed to retrieve the page: {response.status_code}")
                    return []
                
                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all product containers (adjust selector based on the website)
                product_containers = soup.select('.product-item')
                
                products = []
                for container in product_containers:
                    # Extract product details (adjust selectors based on the website)
                    name_elem = container.select_one('.product-name')
                    price_elem = container.select_one('.product-price')
                    
                    if name_elem and price_elem:
                        product = {
                            'name': name_elem.text.strip(),
                            'price': price_elem.text.strip(),
                            'url': container.select_one('a')['href'] if container.select_one('a') else None
                        }
                        products.append(product)
                
                return products
            </pre>
            """
        else:
            return "<p>No specific content available for this URL.</p>"
    
    # Step 4: Create the CodeRAGTool
    rag_tool = CodeRAGTool(web_read_tool)
    
    # Step 5: Get implementation examples from the RAG system
    print("\n=== Getting implementation examples ===")
    implementation_results = await rag_tool.retrieve_implementation_examples(
        feature_description, starter_code, "python"
    )
    
    print("\n" + rag_tool.format_results(implementation_results))
    
    # Step 6: Run the implemented feature (which we created separately)
    print("\n=== Running the implementation ===")
    try:
        # Import the module from the implementation file
        import importlib.util
        implementation_path = Path(__file__).parent / "implemented_scraper.py"
        spec = importlib.util.spec_from_file_location("implemented_scraper", implementation_path)
        implemented_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(implemented_module)
        
        # Run the main function
        implemented_module.main()
        
        # Check if the CSV file was created
        csv_path = Path(__file__).parent / "sample_products.csv"
        if csv_path.exists():
            print(f"\nCSV file created: {csv_path}")
            print("\nCSV content:")
            with open(csv_path, "r") as f:
                print(f.read())
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())