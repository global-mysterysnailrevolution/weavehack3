#!/usr/bin/env python3
"""
Run Biolink Depot pricing comparison using RLM-VLA MCP tools.

This script uses the multi_page_navigation tool to:
1. Navigate to shopbiolinkdepot.org
2. Extract product prices
3. Search Google for each product
4. Compare prices and verify matches
5. Save results to JSON
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rvla.weave_init import ensure_weave_init
from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver

ensure_weave_init()

load_dotenv()


def main():
    """Run the Biolink Depot pricing comparison task."""
    
    print("="*70)
    print("BIOLINK DEPOT PRICING COMPARISON")
    print("Using RLM-VLA Agent with MCP Tools")
    print("="*70)
    print()
    
    # The task description
    goal = """Navigate to https://www.shopbiolinkdepot.org/ and find all products with listed prices. For each product:

1. Take a screenshot of the product page showing the price
2. Search Google for the product name to find actual market prices
3. Compare product images from Google results to confirm it's the same item
4. Identify if the item is only available on eBay or from legitimate vendors
5. Document the pricing difference between shopbiolinkdepot.org and actual market prices
6. Save all findings to a structured JSON file with this format:

{
  "products": [
    {
      "name": "Product Name",
      "shopbiolinkdepot_price": "$X.XX",
      "shopbiolinkdepot_url": "https://www.shopbiolinkdepot.org/product-url",
      "actual_market_price": "$Y.YY",
      "price_difference": "$Z.ZZ",
      "vendor_type": "legitimate_vendor" | "ebay_only" | "both",
      "verified_match": true | false,
      "screenshot_path": "path/to/screenshot.png",
      "google_search_url": "https://google.com/search?q=...",
      "notes": "Any additional observations"
    }
  ],
  "summary": {
    "total_products": 0,
    "overpriced": 0,
    "correctly_priced": 0,
    "underpriced": 0,
    "extraction_date": "YYYY-MM-DD"
  }
}

Important requirements:
- Include the exact shopbiolinkdepot product names and URLs
- Add explicit web search steps (Google/Bing) for each product
- Compare product images to confirm the correct item
- Extract price from reputable vendor pages, not just marketplaces
- Take clear screenshots showing prices
- Verify each product is actually the same item by comparing images
- Document all findings systematically"""
    
    print("Goal:")
    print("-" * 70)
    print(goal[:200] + "...")
    print("-" * 70)
    print()
    
    # Initialize components
    print("[1/3] Initializing workspace and browser...")
    try:
        workspace = workspace_from_env()
        driver = WebDriver()
        print("✅ Initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return 1
    
    print()
    print("[2/3] Running agent...")
    print("This may take several minutes as the agent:")
    print("  - Navigates to shopbiolinkdepot.org")
    print("  - Finds products and prices")
    print("  - Searches Google for each product")
    print("  - Compares images and prices")
    print("  - Documents findings")
    print()
    
    try:
        result = run_agent(
            goal=goal,
            driver=driver,
            workspace=workspace,
            enable_multi_agent=False,  # Single agent for this task
        )
        
        print()
        print("[3/3] Agent execution complete!")
        print("-" * 70)
        print(f"Steps taken: {len(result.get('trajectory', []))}")
        print(f"Events logged: {len(result.get('events', []))}")
        print(f"Score: {result.get('score', {}).get('success_rate', 'N/A')}")
        print("-" * 70)
        print()
        
        # Save results
        output_file = Path(__file__).parent.parent / "biolink_pricing_results.json"
        output_data = {
            "goal": goal,
            "result": {
                "trajectory": [
                    {
                        "type": action.type,
                        "payload": action.payload,
                    }
                    for action in result.get("trajectory", [])
                ],
                "events": result.get("events", []),
                "score": result.get("score", {}),
                "last_observation": {
                    "url": result.get("last_observation", {}).url if result.get("last_observation") else None,
                } if result.get("last_observation") else None,
            },
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        
        print(f"✅ Results saved to: {output_file}")
        print()
        print("Next steps:")
        print("  1. Check the Weave dashboard for detailed traces")
        print("  2. Review the agent's actions in the trajectory")
        print("  3. Look for extracted pricing data in the events")
        print()
        
        # Check if agent found pricing data
        events = result.get("events", [])
        pricing_events = [e for e in events if "price" in str(e).lower() or "pricing" in str(e).lower()]
        if pricing_events:
            print(f"✅ Found {len(pricing_events)} pricing-related events")
            print("   Recent pricing events:")
            for event in pricing_events[-5:]:
                print(f"   - {event[:100]}...")
        else:
            print("⚠️  No pricing events found - agent may need more guidance")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        try:
            driver.close()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
