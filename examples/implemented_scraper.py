"""
Web scraper to extract product prices from e-commerce websites.
"""
import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime

def scrape_product_prices(url, selector_config=None):
    """
    Scrape product prices from an e-commerce website.
    
    Args:
        url: The URL of the e-commerce website
        selector_config: Optional dictionary with CSS selectors for different elements
                        (defaults will be used if not provided)
    
    Returns:
        A list of dictionaries containing product information
    """
    # Default CSS selectors (can be customized for different websites)
    if selector_config is None:
        selector_config = {
            'product_container': '.product-item, .product, .item',
            'product_name': '.product-name, .product-title, h2, h3',
            'product_price': '.product-price, .price, .amount',
            'product_link': 'a',
            'product_image': 'img',
        }
    
    # Add headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        # Send a GET request to the URL
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check if the request was successful
        if response.status_code != 200:
            print(f"Failed to retrieve the page: {response.status_code}")
            return []
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all product containers
        product_containers = soup.select(selector_config['product_container'])
        
        if not product_containers:
            print(f"No products found using selector: {selector_config['product_container']}")
            print("Consider adjusting the selectors for this website.")
            return []
        
        products = []
        for container in product_containers:
            # Extract product details
            name_elem = container.select_one(selector_config['product_name'])
            price_elem = container.select_one(selector_config['product_price'])
            link_elem = container.select_one(selector_config['product_link'])
            image_elem = container.select_one(selector_config['product_image'])
            
            # Skip if essential elements are missing
            if not name_elem or not price_elem:
                continue
            
            # Extract data
            name = name_elem.text.strip()
            price = price_elem.text.strip()
            url = link_elem['href'] if link_elem and 'href' in link_elem.attrs else None
            # Make relative URLs absolute
            if url and not (url.startswith('http://') or url.startswith('https://')):
                base_url = '/'.join(url.split('/')[:3])
                url = f"{base_url}{url}" if url.startswith('/') else f"{base_url}/{url}"
            
            image_url = image_elem['src'] if image_elem and 'src' in image_elem.attrs else None
            
            product = {
                'name': name,
                'price': price,
                'url': url,
                'image_url': image_url,
                'timestamp': datetime.now().isoformat()
            }
            products.append(product)
        
        return products
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

def save_to_csv(products, filename='products.csv'):
    """
    Save the scraped products to a CSV file.
    
    Args:
        products: List of product dictionaries
        filename: Name of the CSV file to save
        
    Returns:
        Boolean indicating success or failure
    """
    if not products:
        print("No products to save.")
        return False
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Get all possible fields from all products
            fieldnames = set()
            for product in products:
                fieldnames.update(product.keys())
            
            writer = csv.DictWriter(csvfile, fieldnames=list(fieldnames))
            writer.writeheader()
            writer.writerows(products)
        
        print(f"Saved {len(products)} products to {filename}")
        return True
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False

def main():
    """Run the web scraper with sample data."""
    # Example usage
    url = "https://example.com/products"  # Replace with actual e-commerce URL
    
    # For demonstration, let's use a different website with custom selectors
    amazon_config = {
        'product_container': '.s-result-item',
        'product_name': 'h2 .a-link-normal',
        'product_price': '.a-price .a-offscreen',
        'product_link': 'h2 .a-link-normal',
        'product_image': '.s-image',
    }
    
    # Uncomment one of these examples to run
    # products = scrape_product_prices(url)  # Using default selectors
    # products = scrape_product_prices("https://www.amazon.com/s?k=laptop", amazon_config)
    
    # For demonstration purposes, let's create some sample data
    sample_products = [
        {'name': 'Laptop XPS 13', 'price': '$999.99', 'url': 'https://example.com/laptop-xps-13'},
        {'name': 'Wireless Mouse', 'price': '$24.99', 'url': 'https://example.com/wireless-mouse'},
        {'name': 'Mechanical Keyboard', 'price': '$89.99', 'url': 'https://example.com/mechanical-keyboard'},
    ]
    
    # Save the products to a CSV file
    save_to_csv(sample_products, 'sample_products.csv')
    
    # Print the products
    print(f"Found {len(sample_products)} products:")
    for product in sample_products:
        print(f"{product['name']}: {product['price']}")

if __name__ == "__main__":
    main()