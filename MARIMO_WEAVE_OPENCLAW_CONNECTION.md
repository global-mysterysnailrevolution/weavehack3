# Marimo ↔ Weave ↔ OpenClaw Connection Guide

## Overview

This document explains how Marimo, Weave, and OpenClaw are connected to show agent improvements, prompt updates, and run analysis in real-time.

## Architecture

```
┌─────────────────┐
│  OpenClaw CLI   │
│  (Beach/Sea)    │
└────────┬────────┘
         │
         │ Runs via subprocess
         ▼
┌─────────────────┐
│  FastAPI Backend│
│  (api/main.py)  │
│                 │
│  - Captures     │
│    full logs    │
│  - Analyzes     │
│    output       │
│  - Scores runs  │
│  - Generates    │
│    suggestions  │
└────────┬────────┘
         │
         │ @weave.op()
         │ record_openclaw_run()
         ▼
┌─────────────────┐
│  Weave          │
│  (Observability)│
│                 │
│  Stores:        │
│  - Mode         │
│  - Goal         │
│  - Iteration    │
│  - Exit code    │
│  - Events       │
│  - Analysis     │
│    (score,      │
│     suggestions)│
└────────┬────────┘
         │
         │ weave.get_calls()
         │ weave.get_call(id)
         ▼
┌─────────────────┐
│  Marimo         │
│  Dashboard      │
│                 │
│  - Queries      │
│    Weave        │
│  - Extracts     │
│    OpenClaw     │
│    runs         │
│  - Shows scores │
│  - Displays     │
│    suggestions  │
│  - Tracks       │
│    prompt       │
│    evolution    │
└────────┬────────┘
         │
         │ iframe embed
         ▼
┌─────────────────┐
│  Next.js Web UI │
│  (Vercel)       │
│                 │
│  - MarimoEmbed  │
│    component    │
│  - Auto-refresh │
│    on complete  │
│  - Shows status │
└─────────────────┘
```

## Data Flow

### 1. OpenClaw Run Execution

When you click "Run on the Beach" or "Cook Longer":

1. **Frontend** (`OpenClawBeachPanel.tsx`):
   - Sends POST to `/api/openclaw/beach` or `/api/openclaw/sea`
   - Streams SSE events (logs, events, scores, suggestions)

2. **Next.js Proxy** (`web/app/api/openclaw/[mode]/route.ts`):
   - Forwards request to FastAPI backend
   - Streams response back to frontend

3. **FastAPI Backend** (`api/main.py`):
   - Executes OpenClaw CLI command
   - Captures all output lines and events
   - Analyzes output for:
     - Error patterns
     - Success indicators
     - Task-specific keywords (e.g., "shopbiolinkdepot", "pricing")
   - Calculates score (0.0-1.0)
   - Generates prompt improvement suggestions
   - Logs to Weave via `record_openclaw_run()`

### 2. Weave Logging

The `record_openclaw_run()` function (decorated with `@weave.op()`) stores:

```python
{
    "mode": "beach" | "sea",
    "goal": "task description",
    "iteration": 0, 1, 2, ...
    "exit_code": 0 | None,
    "output_tail": ["last 50 lines of output"],
    "events": [{"type": "...", ...}, ...],
    "analysis": {
        "score": 0.75,
        "error_hits": 2,
        "success_hits": 5,
        "pricing_hits": 8,
        "suggestions": [
            "Include the exact shopbiolinkdepot product names and URLs.",
            "Add explicit web search steps (Google/Bing) for each product.",
            ...
        ]
    }
}
```

### 3. Prompt Evolution

When you click "Cook Longer" (iteration > 0):

1. Backend loads previous state from `.beach_state.json`
2. Appends previous output tail to goal
3. **Adds patch suggestions** from last analysis:
   ```
   {goal}
   
   Previous beach notes:
   {last_output_tail}
   
   Patch suggestions:
   - {suggestion 1}
   - {suggestion 2}
   ...
   ```
4. Runs OpenClaw again with improved prompt
5. Logs new run to Weave

### 4. Marimo Dashboard

The Marimo notebook (`marimo/weave_dashboard.py`):

1. **Initializes Weave**:
   ```python
   weave.init(project="weavehacks-rvla", entity=...)
   ```

2. **Queries Weave**:
   ```python
   calls = weave.get_calls()
   recent_calls = calls.head(100)
   ```

3. **Extracts OpenClaw Runs**:
   - Filters calls where `op_name` contains "record_openclaw_run"
   - Accesses call output/return value
   - Extracts analysis data (scores, suggestions)

4. **Displays**:
   - Run summary table (mode, iteration, score, exit code)
   - Latest suggestions
   - Prompt evolution across iterations
   - Performance trends

### 5. Web UI Integration

The `MarimoEmbed` component:

- Embeds Marimo dashboard via iframe
- **Auto-refreshes** when execution completes (2s delay for Weave sync)
- Shows status messages for OpenClaw runs
- Provides manual refresh button

## Verification Steps

### 1. Check Weave Connection

In Marimo dashboard, you should see:
```
✅ Initialized Weave: entity/project
```

If you see `❌ Failed to initialize Weave`, check:
- `WANDB_API_KEY` is set
- `WANDB_PROJECT` is set (default: "weavehacks-rvla")
- `WANDB_ENTITY` is set (your W&B username)

### 2. Check OpenClaw Runs Are Logged

1. Run an OpenClaw task via "Run on the Beach"
2. Wait for completion
3. In Marimo dashboard, scroll to "🦀 OpenClaw Runs & Analysis"
4. You should see:
   - A table with your runs
   - Scores (0.0-1.0)
   - Number of suggestions
   - Exit codes

### 3. Check Prompt Evolution

1. Run "Run on the Beach" (iteration 0)
2. Wait for completion
3. Click "Cook Longer" (iteration 1)
4. In Marimo dashboard, scroll to "📈 Prompt Evolution"
5. You should see:
   - Iteration 0 with its score and suggestions
   - ↓ "Next iteration incorporates feedback" ↓
   - Iteration 1 with updated score

### 4. Check Suggestions Are Applied

In the Marimo dashboard "Latest Prompt Suggestions" section, you should see:
- Specific, actionable suggestions
- Suggestions that reference your task (e.g., "shopbiolinkdepot", "pricing")

## Troubleshooting

### Marimo Dashboard Shows "No OpenClaw runs found"

**Possible causes:**
1. Weave not initialized correctly
2. `record_openclaw_run` not being called
3. Weave call output not accessible

**Solutions:**
- Check FastAPI logs for `record_openclaw_run` calls
- Verify `WANDB_API_KEY` is set in Marimo environment
- Check Weave project name matches

### Scores Always Show "N/A"

**Possible causes:**
- Weave call output not accessible via `.output` or `.result`
- Analysis dict not in expected format

**Solutions:**
- Check `api/main.py` `_analyze_openclaw_output()` is being called
- Verify `record_openclaw_run()` returns the analysis dict
- Check Marimo dashboard error messages

### Prompt Suggestions Not Appearing

**Possible causes:**
- `_analyze_openclaw_output()` not generating suggestions
- Suggestions not being passed to `record_openclaw_run()`

**Solutions:**
- Check FastAPI logs for analysis output
- Verify suggestions are in the analysis dict
- Check `.beach_state.json` contains `last_analysis`

### Auto-Refresh Not Working

**Possible causes:**
- Execution status not updating correctly
- iframe not reloading

**Solutions:**
- Check browser console for errors
- Verify `execution.status === 'completed'` is being set
- Try manual refresh button

## Environment Variables

### FastAPI Backend
- `WANDB_API_KEY` - Weights & Biases API key
- `WANDB_PROJECT` - Weave project name (default: "weavehacks-rvla")
- `WANDB_ENTITY` - W&B entity/username
- `OPENCLAW_BEACH_CMD` - Command to run OpenClaw in sandbox mode (default: "openclaw agent --message")
- `OPENCLAW_SEA_CMD` - Command to run OpenClaw in production mode

### Marimo Dashboard
- `WANDB_API_KEY` - Same as above
- `WANDB_PROJECT` - Same as above
- `WANDB_ENTITY` - Same as above
- `WEAVE_CALL_LIMIT` - Max calls to fetch (default: 100)

### Next.js Frontend
- `NEXT_PUBLIC_API_BASE_URL` - FastAPI backend URL (e.g., "http://localhost:8000")
- `MARIMO_PROXY_URL` - Published Marimo notebook URL (e.g., "https://marimo.app/l/...")
- `NEXT_PUBLIC_MARIMO_URL` - Override for Marimo URL (optional)

## Next Steps

1. **Run OpenClaw tasks** via the Beach panel
2. **Watch Marimo dashboard** for scores and suggestions
3. **Click "Cook Longer"** to see prompt evolution
4. **Review suggestions** and verify they're being applied
5. **Compare scores** across iterations to see improvement

The system is designed to be self-improving: each iteration incorporates feedback from the previous run, leading to better prompts and higher scores over time.
