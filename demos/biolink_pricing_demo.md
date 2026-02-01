# Biolink Depot Pricing Demo: Iterative Improvement

This demo shows how the OpenClaw Beach/Sea system improves over multiple iterations when extracting and verifying pricing data from shopbiolinkdepot.org.

## Demo Goal

Extract pricing data from shopbiolinkdepot.org, verify actual market prices via Google search, compare product images, and document pricing discrepancies.

## Prerequisites

1. **OpenClaw installed and configured**
   ```bash
   # Install OpenClaw
   npm i -g openclaw
   # or
   curl -fsSL https://openclaw.ai/install.sh | bash
   ```

2. **Environment variables set:**
   - `OPENAI_API_KEY` - For RLM-VLA agent
   - `BROWSERBASE_API_KEY` - For browser automation
   - `BROWSERBASE_PROJECT_ID` - Browserbase project
   - `WANDB_API_KEY` - For Weave observability
   - `WANDB_PROJECT` - Weave project (default: "weavehacks-rvla")
   - `WANDB_ENTITY` - Your W&B username

3. **FastAPI backend running:**
   ```bash
   cd api
   python main.py
   # or
   uvicorn main:app --reload
   ```

4. **Next.js frontend running:**
   ```bash
   cd web
   npm run dev
   ```

5. **Marimo dashboard published:**
   - Publish `marimo/weave_dashboard.py` to marimo.app
   - Set `MARIMO_PROXY_URL` in Vercel environment variables

## Demo Steps

### Step 1: Initial Run (Iteration 0) - "Run on the Beach"

**Task:**
```
Navigate to https://www.shopbiolinkdepot.org/ and find all products with listed prices. For each product:
1. Take a screenshot of the product page showing the price
2. Search Google for the product name to find actual market prices
3. Compare product images from Google results to confirm it's the same item
4. Identify if the item is only available on eBay or from legitimate vendors
5. Document the pricing difference between shopbiolinkdepot.org and actual market prices
6. Save all findings to a structured JSON file
```

**Expected Issues (First Run):**
- May miss some products
- May not take screenshots of prices
- May not properly compare images
- May not verify vendor legitimacy
- May not document findings clearly

**What to Watch:**
- Check the score (likely 0.5-0.7)
- Review suggestions in the UI
- Note which steps were missed

### Step 2: Review Suggestions

After the first run completes, the system will generate suggestions like:

- "Include the exact shopbiolinkdepot product names and URLs."
- "Add explicit web search steps (Google/Bing) for each product."
- "Compare product images to confirm the correct item."
- "Extract price from reputable vendor pages, not marketplaces."
- "Add recovery steps for errors and retry navigation."

### Step 3: Iterate - "Cook Longer" (Iteration 1)

Click **"Cook Longer"** to run again with improved prompt.

The new prompt will include:
- Previous run's output tail
- All suggestions from the analysis

**Expected Improvements:**
- More thorough product discovery
- Better screenshot capture
- More systematic Google searches
- Image comparison logic
- Vendor verification
- Better documentation

**What to Watch:**
- Score should improve (0.7-0.9)
- More products found
- Better structured output
- Fewer errors

### Step 4: Continue Iterating (Optional)

Run "Cook Longer" again if needed:
- Iteration 2: Refine image comparison
- Iteration 3: Improve vendor verification
- Iteration 4: Enhance documentation format

### Step 5: Release to Sea (Final)

Once score is consistently high (>0.8) and output looks good:

Click **"Release to Sea"** to run in production mode (non-sandbox).

This executes the final, improved version.

## What to Observe in Marimo Dashboard

### 1. OpenClaw Runs & Analysis

You should see a table like:

| Mode | Iteration | Score | Exit | Suggestions |
|------|-----------|-------|------|-------------|
| beach | 0 | 0.65 | 0 | 4 |
| beach | 1 | 0.82 | 0 | 2 |
| beach | 2 | 0.88 | 0 | 1 |
| sea | 0 | 0.91 | 0 | 0 |

### 2. Prompt Evolution

The dashboard shows how the prompt improves:

**Iteration 0:**
- Basic task description
- Score: 0.65

**Iteration 1:**
- Includes previous output
- Adds: "Include the exact shopbiolinkdepot product names and URLs"
- Adds: "Add explicit web search steps (Google/Bing) for each product"
- Score: 0.82

**Iteration 2:**
- Includes all previous feedback
- Adds: "Compare product images to confirm the correct item"
- Score: 0.88

### 3. Performance Trends

Track improvements in:
- Execution speed
- Success rate
- Product discovery count
- Error reduction

## Expected Output

After successful runs, you should have:

1. **Screenshots** of product pages with prices
2. **Google search results** for each product
3. **Image comparisons** confirming product matches
4. **Vendor analysis** (eBay vs legitimate vendors)
5. **Pricing comparison** JSON file with:
   ```json
   {
     "products": [
       {
         "name": "Product Name",
         "shopbiolinkdepot_price": "$X.XX",
         "actual_market_price": "$Y.YY",
         "price_difference": "$Z.ZZ",
         "vendor_type": "legitimate_vendor" | "ebay_only" | "both",
         "verified_match": true | false,
         "screenshot_path": "path/to/screenshot.png",
         "google_search_url": "https://google.com/search?..."
       }
     ],
     "summary": {
       "total_products": 10,
       "overpriced": 7,
       "correctly_priced": 2,
       "underpriced": 1
     }
   }
   ```

## Success Criteria

✅ **Iteration 0:**
- Finds at least 3 products
- Takes at least 1 screenshot
- Attempts Google search
- Score: 0.5-0.7

✅ **Iteration 1:**
- Finds 5+ products
- Screenshots for all products
- Systematic Google searches
- Image comparison attempts
- Score: 0.7-0.9

✅ **Iteration 2+:**
- Finds all visible products
- Complete documentation
- Accurate price comparisons
- Vendor verification
- Score: 0.8-1.0

## Troubleshooting

### Low Scores (<0.5)

**Possible causes:**
- OpenClaw not finding products
- Browser automation failing
- Network errors

**Solutions:**
- Check Browserbase connection
- Verify shopbiolinkdepot.org is accessible
- Review error logs in the UI

### Suggestions Not Being Applied

**Possible causes:**
- State file not saving
- Prompt not including suggestions

**Solutions:**
- Check `.beach_state.json` exists
- Verify FastAPI logs show suggestions in prompt
- Check Marimo dashboard for prompt evolution

### No Improvement Between Iterations

**Possible causes:**
- Suggestions too generic
- Task too complex
- OpenClaw limitations

**Solutions:**
- Review suggestions - may need manual refinement
- Break task into smaller subtasks
- Consider using RLM-VLA agent directly for web tasks

## Next Steps

After the demo:

1. **Analyze the results** - Review pricing discrepancies
2. **Export findings** - Share pricing comparison report
3. **Iterate further** - Continue improving for other stores
4. **Scale up** - Apply to multiple product categories

## Video Walkthrough (Optional)

Record a screen capture showing:
1. Initial run with low score
2. Suggestions appearing
3. "Cook Longer" click
4. Improved run with higher score
5. Marimo dashboard showing evolution
6. Final "Release to Sea"

This demonstrates the self-improving nature of the system!
