# Biolink Depot Pricing Demo

This demo showcases the iterative improvement capabilities of the OpenClaw Beach/Sea system when extracting and verifying pricing data.

## Quick Start

### Option 1: Web UI (Recommended)

1. **Start the backend:**
   ```bash
   cd api
   python main.py
   ```

2. **Start the frontend:**
   ```bash
   cd web
   npm run dev
   ```

3. **Open the web UI:**
   - Navigate to `http://localhost:3000`
   - Paste the task from `biolink_pricing_task.txt` into the OpenClaw Beach panel
   - Click "Run on the Beach"
   - Watch the score and suggestions
   - Click "Cook Longer" to iterate
   - Check the Marimo dashboard for visualization

### Option 2: Python Script

```bash
# Set API base URL
export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Run the demo script
python demos/run_biolink_demo.py
```

## Files

- **`biolink_pricing_demo.md`** - Complete demo guide with step-by-step instructions
- **`biolink_pricing_task.txt`** - The task description to use
- **`run_biolink_demo.py`** - Automated demo script
- **`README.md`** - This file

## What the Demo Shows

1. **Initial Run (Iteration 0)**
   - Basic task execution
   - Score: ~0.5-0.7
   - Generates improvement suggestions

2. **Iteration 1 (Cook Longer)**
   - Incorporates suggestions from iteration 0
   - Score: ~0.7-0.9
   - More thorough execution

3. **Iteration 2+ (Optional)**
   - Further refinement
   - Score: ~0.8-1.0
   - Production-ready

4. **Release to Sea**
   - Final execution in production mode
   - Uses best prompt from iterations

## Expected Improvements

- **Product Discovery**: More products found in later iterations
- **Screenshot Quality**: Better screenshots showing prices
- **Search Coverage**: More systematic Google searches
- **Image Comparison**: Better product matching
- **Documentation**: More structured JSON output
- **Error Handling**: Fewer errors, better recovery

## Marimo Dashboard

After running iterations, check the Marimo dashboard to see:

- **OpenClaw Runs Table**: Scores, iterations, exit codes
- **Prompt Evolution**: How the prompt improves across iterations
- **Performance Trends**: Execution speed, success rates
- **Improvement Suggestions**: What changed between runs

## Troubleshooting

See `biolink_pricing_demo.md` for detailed troubleshooting steps.

## Next Steps

1. Run the demo and observe improvements
2. Check Marimo dashboard for visualization
3. Export results and analyze pricing discrepancies
4. Apply to other stores or product categories
