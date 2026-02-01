# OpenClaw vs RLM-VLA Agent - Clarification

## The Issue

You were right to question this! The codebase references "OpenClaw" extensively, but **OpenClaw is not actually installed or connected**. The code was trying to run a CLI command `openclaw agent --message` that doesn't exist.

## What Actually Exists

The **RLM-VLA agent** is the real agent that exists in this codebase:
- Located in `src/rvla/agent.py`
- Uses `run_agent()` function
- Has web navigation, visual analysis, and RLM context examination
- Already integrated via `/api/agent/run` endpoint

## What Was Fixed

I've replaced the fake OpenClaw calls with the actual RLM-VLA agent:

### Before (Broken):
```python
# Tried to run non-existent CLI command
base_cmd = "openclaw agent --message"
process = subprocess.Popen(cmd, ...)
```

### After (Fixed):
```python
# Uses actual RLM-VLA agent
from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver

result = run_agent(
    goal=goal,
    driver=driver,
    workspace=workspace,
    enable_multi_agent=True,
)
```

## What "OpenClaw Beach" Actually Is Now

The `/api/openclaw/beach` and `/api/openclaw/sea` endpoints now:
1. **Use the RLM-VLA agent** (not OpenClaw)
2. **Beach mode** = Same as regular, just labeled for sandboxing concept
3. **Sea mode** = Same as regular, just labeled for production concept
4. **Still support** the iterative improvement loop with Redis prompt database
5. **Still log to Weave** for analysis

## Why Keep the "OpenClaw" Name?

The UI and API endpoints still use "OpenClaw" naming because:
- The frontend components are already built with that name
- The concept (sandboxed iterative improvement) still applies
- It's easier than refactoring all the UI components

But internally, it's **100% the RLM-VLA agent**.

## What OpenClaw Was Supposed To Be

OpenClaw was intended to be:
- A separate agent framework (like Gastown)
- Would handle file operations, calendar, email, etc.
- Would be called via MCP (Model Context Protocol)
- But it was never actually installed or integrated

## Current Architecture

```
User Request
    ↓
/api/openclaw/beach or /api/openclaw/sea
    ↓
_stream_openclaw() function
    ↓
RLM-VLA Agent (src/rvla/agent.py)
    ↓
- WebDriver for navigation
- Workspace for memory
- Weave for tracing
- Redis for prompt database
    ↓
Results streamed back via SSE
```

## Summary

- ✅ **RLM-VLA agent** = Real, working, integrated
- ❌ **OpenClaw** = Never existed, was a placeholder
- ✅ **"OpenClaw Beach" endpoints** = Now use RLM-VLA agent
- ✅ **Redis prompt database** = Still works, learns from RLM-VLA runs
- ✅ **Weave integration** = Still works, traces RLM-VLA agent

The system is now **actually functional** instead of trying to call a non-existent tool!
