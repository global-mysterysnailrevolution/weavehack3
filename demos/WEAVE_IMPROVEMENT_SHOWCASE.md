# Weave-Driven Iterative Improvement Showcase

This demo showcases how Weave traces enable iterative improvement of the RLM-VLA agent for the Biolink Depot pricing task.

## Overview

The showcase demonstrates:
1. **Initial Run** - Agent attempts the task, all actions logged to Weave
2. **Analysis** - Weave traces analyzed to identify issues and patterns
3. **Improvement** - Suggestions generated from trace analysis
4. **Iteration** - Agent runs again with improved prompts
5. **Comparison** - Results compared across iterations
6. **Visualization** - Marimo dashboard shows improvement trends

## How It Works

### 1. Weave Tracing

Every agent execution is automatically traced to Weave:
- All actions (navigate, click, extract, etc.)
- All observations (screenshots, page state)
- All events (success, errors, milestones)
- Performance metrics (steps, duration, success rate)

### 2. Trace Analysis

After each iteration, the system analyzes Weave traces to identify:
- **Missing actions** - Did agent navigate to the store? Search Google?
- **Incomplete tasks** - Did agent extract prices? Compare images?
- **Inefficiencies** - Too few steps? Too many errors?
- **Success patterns** - What worked well?

### 3. Improvement Generation

Based on trace analysis, the system generates specific suggestions:
- "Add explicit navigation step: 'Navigate to https://www.shopbiolinkdepot.org/'"
- "Add explicit Google search steps for each product"
- "Take screenshots of product pages showing prices"
- "Explicitly extract and document prices from both sources"

### 4. Iterative Refinement

Each iteration incorporates feedback:
- Previous issues are addressed
- Suggestions are added to the prompt
- Agent runs with improved guidance
- Results are compared

### 5. Visualization

Marimo dashboard shows:
- Iteration comparison table
- Improvement trends (steps, events, success)
- Weave trace links for each iteration
- Performance metrics over time

## Running the Showcase

### Option 1: Python Script (Automated)

```bash
# Set number of iterations (default: 3)
export WEAVE_ITERATIONS=3

# Run the showcase
python scripts/showcase_weave_improvement.py
```

The script will:
1. Run iteration 1 with base goal
2. Analyze results and generate feedback
3. Run iteration 2 with improvements
4. Analyze and iterate again
5. Compare all iterations
6. Save results to `weave_improvement_showcase.json`

### Option 2: Manual Iteration via Web UI

1. **First Run:**
   - Paste base goal in web UI
   - Run agent
   - Check Weave traces for issues

2. **Analyze:**
   - Review Marimo dashboard
   - Identify missing actions
   - Note improvement opportunities

3. **Second Run:**
   - Add improvements to goal
   - Run again
   - Compare results

4. **Iterate:**
   - Continue refining based on Weave analysis
   - Track improvement over iterations

## Expected Improvements

### Iteration 1 (Baseline)
- May miss some products
- May not search Google
- May not compare images
- May not document findings
- **Issues:** 3-5 identified
- **Success:** Partial

### Iteration 2 (With Improvements)
- More thorough product discovery
- Explicit Google searches
- Image comparison attempts
- Better documentation
- **Issues:** 1-3 remaining
- **Success:** Improved

### Iteration 3 (Refined)
- Complete product coverage
- Systematic price comparison
- Verified image matches
- Structured JSON output
- **Issues:** 0-1 minor
- **Success:** High

## What to Observe

### In Weave Dashboard

1. **Call Tree:**
   - See all function calls
   - Compare call patterns between iterations
   - Identify new calls added in later iterations

2. **Execution Traces:**
   - View full action sequences
   - Compare trajectory lengths
   - See which actions were added

3. **Performance Metrics:**
   - Steps per iteration
   - Success rates
   - Error counts
   - Duration trends

### In Marimo Dashboard

1. **Iteration Comparison:**
   - Table showing all iterations
   - Metrics side-by-side
   - Clear improvement indicators

2. **Improvement Trends:**
   - Steps increasing (more thorough)
   - Success rate improving
   - Issues decreasing

3. **OpenClaw Runs:**
   - If using OpenClaw Beach, see scores improving
   - Suggestions being applied
   - Prompt evolution

## Key Metrics to Track

- **Steps:** Should increase (more thorough execution)
- **Events:** Should increase (better logging)
- **Success:** Should improve (task completion)
- **Issues:** Should decrease (fewer problems)
- **Score:** Should increase (better quality)

## Example Output

```
ITERATION 1/3
- Steps: 8
- Events: 12
- Success: False
- Issues: 4 (no navigation, no search, no screenshots, no pricing)

ITERATION 2/3
- Steps: 15
- Events: 28
- Success: True
- Issues: 1 (incomplete documentation)

ITERATION 3/3
- Steps: 22
- Events: 45
- Success: True
- Issues: 0

Improvement: Steps 8→22 (+14), Success False→True ✅
```

## Best Practices

1. **Start Simple:** Begin with basic goal, let Weave identify gaps
2. **Iterate Gradually:** Add improvements one at a time
3. **Compare Traces:** Look at Weave traces between iterations
4. **Track Metrics:** Monitor steps, events, success rates
5. **Use Feedback:** Incorporate suggestions from analysis
6. **Visualize:** Check Marimo dashboard for trends

## Integration with OpenClaw Beach

You can combine this with OpenClaw Beach for even better iteration:

1. Run iteration in OpenClaw Beach
2. Get score and suggestions
3. Use suggestions to improve next iteration
4. Track in Weave and Marimo
5. Compare Beach scores across iterations

## Next Steps

After running the showcase:

1. **Review Weave Traces:** Deep dive into what changed
2. **Export Results:** Save improvement data
3. **Share Findings:** Document what worked
4. **Apply to Other Tasks:** Use same approach for different goals
5. **Automate:** Set up continuous improvement loop

The power of Weave is that it provides **observability** → **analysis** → **improvement** → **verification** in a continuous loop!
