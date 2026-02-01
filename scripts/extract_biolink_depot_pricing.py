"""Extract accurate pricing from Biolink Depot store."""

import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def fetch_page(url: str, retries: int = 3) -> str:
    """Fetch HTML content from a URL with retries."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return ""

def extract_product_links(html: str, base_url: str) -> list[str]:
    """Extract product page URLs from the main products page."""
    soup = BeautifulSoup(html, 'html.parser')
    product_links = []
    
    # Look for product links - common patterns in e-commerce
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        # Look for product links (often contain product IDs or /product/ paths)
        if any(pattern in href.lower() for pattern in ['product', 'item', 'view', 'quick']):
            full_url = urljoin(base_url, href)
            if full_url not in product_links:
                product_links.append(full_url)
    
    # Also look for data attributes that might contain product URLs
    for element in soup.find_all(attrs={'data-product-url': True}):
        url = element.get('data-product-url')
        if url:
            product_links.append(urljoin(base_url, url))
    
    return product_links[:50]  # Limit to first 50 for now

def extract_price_from_text(text: str) -> str | None:
    """Extract price string from text using regex."""
    # Look for price patterns: $XX.XX, $X,XXX.XX, etc.
    price_patterns = [
        r'\$[\d,]+\.?\d*',  # $99.99, $1,234.56
        r'USD\s*[\d,]+\.?\d*',  # USD 99.99
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None

def extract_product_info_from_page(html: str, url: str) -> dict | None:
    """Extract product information from a product page."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try to find product name
    name = None
    for selector in ['h1', '.product-name', '.product-title', '[itemprop="name"]']:
        element = soup.select_one(selector)
        if element:
            name = element.get_text(strip=True)
            break
    
    # Try to find price
    price = None
    price_selectors = [
        '.price', '.product-price', '[itemprop="price"]', 
        '.current-price', '.sale-price', '.regular-price'
    ]
    for selector in price_selectors:
        element = soup.select_one(selector)
        if element:
            price_text = element.get_text(strip=True)
            price = extract_price_from_text(price_text)
            if price:
                break
    
    # If no structured price found, search entire page
    if not price:
        page_text = soup.get_text()
        price = extract_price_from_text(page_text)
    
    # Try to find SKU/product code
    sku = None
    for selector in ['.sku', '[itemprop="sku"]', '.product-code']:
        element = soup.select_one(selector)
        if element:
            sku = element.get_text(strip=True)
            break
    
    if name and price:
        return {
            "name": name,
            "price": price,
            "sku": sku,
            "url": url
        }
    return None

def extract_product_section(html: str) -> str:
    """Extract just the product listing section from HTML to reduce token usage."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for product containers
    product_sections = []
    
    # Common product container selectors
    selectors = [
        '.products', '.product-list', '.product-grid', 
        '.product-items', '[class*="product"]', 'main', 'article'
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            for elem in elements[:5]:  # Limit to first 5 matches
                text = elem.get_text(separator=' ', strip=True)
                if len(text) > 100:  # Only include substantial content
                    product_sections.append(text[:5000])  # Limit each section
    
    if product_sections:
        return '\n\n'.join(product_sections[:10])  # Combine first 10 sections
    
    # Fallback: extract all text but limit length
    return soup.get_text(separator=' ', strip=True)[:20000]

def extract_all_products_with_gpt4o(html: str, url: str) -> dict:
    """Use GPT-4o to extract all product pricing from the main products page."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Extract just the product section to reduce tokens
    product_text = extract_product_section(html)
    print(f"Extracted product section: {len(product_text)} characters")
    
    prompt = f"""Extract ALL product pricing information from this Biolink Depot store page.

URL: {url}

IMPORTANT: Extract the ACCURATE prices for each product. Look carefully at the price displayed for each item.

Return a JSON object with this structure:
{{
  "products": [
    {{
      "name": "exact product name as shown",
      "price": "exact price as displayed (e.g., $99.99)",
      "product_code": "product code/SKU if visible",
      "description": "brief description if available"
    }}
  ],
  "store_name": "Biolink Depot",
  "currency": "USD",
  "total_products": number of products found
}}

Extract EVERY product you can see on this page with its accurate price.

Product listing content:
{product_text}
"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a data extraction expert. Extract ALL product pricing data accurately from HTML. Pay close attention to the exact prices displayed. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    return json.loads(content)

def main():
    base_url = "https://www.shopbiolinkdepot.org"
    products_url = f"{base_url}/"
    
    print(f"Fetching main page: {products_url}")
    html = fetch_page(products_url)
    print(f"Fetched {len(html)} characters")
    
    print("\nExtracting all products with GPT-4o...")
    result = extract_all_products_with_gpt4o(html, products_url)
    
    print(f"\nFound {result.get('total_products', len(result.get('products', [])))} products")
    
    # Also try to extract product links and verify prices from individual pages
    print("\nExtracting product links for verification...")
    product_links = extract_product_links(html, base_url)
    print(f"Found {len(product_links)} potential product links")
    
    # Verify prices from individual product pages (sample first 10)
    verified_products = []
    if product_links:
        print("\nVerifying prices from individual product pages (sampling first 10)...")
        for i, link in enumerate(product_links[:10], 1):
            try:
                print(f"  Checking product {i}/{min(10, len(product_links))}: {link}")
                product_html = fetch_page(link)
                product_info = extract_product_info_from_page(product_html, link)
                if product_info:
                    verified_products.append(product_info)
                time.sleep(1)  # Be polite
            except Exception as e:
                print(f"    Error: {e}")
                continue
    
    # Merge results
    if verified_products:
        result["verified_products"] = verified_products
        result["verification_note"] = f"Verified {len(verified_products)} products from individual pages"
    
    print("\n" + "="*60)
    print("BIOLINK DEPOT - ACCURATE PRICING DATA")
    print("="*60)
    print(json.dumps(result, indent=2))
    
    # Save to file
    output_file = Path(__file__).parent.parent / "biolink_depot_accurate_pricing.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Saved to: {output_file}")
    
    # Also create a CSV-friendly summary
    summary = {
        "store": result.get("store_name", "Biolink Depot"),
        "total_products": result.get("total_products", len(result.get("products", []))),
        "products": result.get("products", [])
    }
    summary_file = Path(__file__).parent.parent / "biolink_depot_pricing_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[OK] Summary saved to: {summary_file}")

if __name__ == "__main__":
    main()
