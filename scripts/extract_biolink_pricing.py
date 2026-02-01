"""Quick script to extract Biolink Depot pricing using HTTP requests + GPT-4o."""

import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def fetch_page_html(url: str) -> str:
    """Fetch HTML content from a URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text

def extract_pricing_with_gpt4o(html: str, url: str) -> dict:
    """Use GPT-4o to extract pricing data from HTML."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Truncate HTML if too long (keep first 100k chars)
    html_preview = html[:100000] if len(html) > 100000 else html
    
    prompt = f"""Extract all product pricing information from this HTML page.

URL: {url}

Return a JSON object with this structure:
{{
  "products": [
    {{
      "name": "product name",
      "price": "price string",
      "description": "brief description if available",
      "url": "product URL if available"
    }}
  ],
  "store_name": "store name",
  "currency": "USD or other"
}}

HTML content:
{html_preview}
"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a data extraction expert. Extract structured pricing data from HTML. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    return json.loads(content)

def main():
    url = "https://biolinkdepot.com"
    
    print(f"Fetching {url}...")
    html = fetch_page_html(url)
    print(f"Fetched {len(html)} characters")
    
    print("Extracting pricing data with GPT-4o...")
    result = extract_pricing_with_gpt4o(html, url)
    
    print("\n" + "="*60)
    print("BIOLINK DEPOT PRICING DATA")
    print("="*60)
    print(json.dumps(result, indent=2))
    
    # Save to file
    output_file = Path(__file__).parent.parent / "biolink_depot_pricing.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n[OK] Saved to: {output_file}")

if __name__ == "__main__":
    main()
