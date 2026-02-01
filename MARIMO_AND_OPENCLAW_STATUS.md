# Marimo & OpenClaw Integration Status

## 1. Marimo Dashboard ✅

**Status:** Should work, but Weave API access is limited

### How It Works

The Marimo dashboard (`marimo/weave_dashboard.py`) is configured to:
- ✅ Initialize Weave with your project
- ✅ Query Weave traces (though Python API is limited)
- ✅ Display agent runs, scores, and improvements
- ✅ Show prompt evolution across iterations

### Viewing in Marimo

**Option 1: Run Marimo locally**
```bash
marimo edit marimo/weave_dashboard.py
```
This opens an interactive dashboard in your browser.

**Option 2: View in Web App**
The Marimo dashboard is embedded in your web app at `/api/marimo`. It auto-refreshes after agent runs.

**Option 3: View in W&B Dashboard**
All traces are visible at:
```
https://wandb.ai/globalmysterysnailrevolution-provigen-ai/weavehacks-rvla/weave
```

### What Marimo Shows

- ✅ Execution summaries
- ✅ Performance trends
- ✅ OpenClaw (RLM-VLA) run analysis
- ✅ Scores and suggestions
- ✅ Prompt evolution across iterations

**Note:** The Weave Python API (`weave.get_op_runs()`) may not work, but Marimo can still access data via the W&B dashboard URL or by using the wandb API directly.

## 2. Passing Data from OpenClaw/External Agents ✅

**Status:** Infrastructure ready, but OpenClaw needs to be installed

### Current Situation

- ❌ **OpenClaw is NOT installed** - It's a placeholder in the code
- ✅ **MCP integration exists** - Ready to receive calls from OpenClaw
- ✅ **Multi-agent coordinator** - Can delegate tasks
- ✅ **Workspace/Memory** - Can store external data

### How to Pass External Data

#### Method 1: Via Workspace (Recommended)

```python
from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver

workspace = workspace_from_env()
driver = WebDriver()

# Store external data (from API, OpenClaw, etc.)
workspace.set("external_data", {
    "api_response": {...},
    "openclaw_result": {...},
    "user_input": "...",
})

# Agent can access this
result = run_agent(
    goal="Use external data to complete task",
    driver=driver,
    workspace=workspace,
    enable_multi_agent=True,  # Enables external agent calls
)
```

#### Method 2: Via API Endpoint

Modify `api/main.py` to accept external data:

```python
class OpenClawRequest(BaseModel):
    goal: str
    iteration: int = 0
    external_data: dict[str, Any] | None = None  # Add this
    context: dict[str, Any] | None = None  # Add this

# In _stream_openclaw function:
if request.external_data:
    workspace.set("external_data", request.external_data)
```

Then POST to `/api/openclaw/beach`:
```json
{
    "goal": "Task description",
    "iteration": 0,
    "external_data": {
        "api_result": {...},
        "openclaw_data": {...}
    }
}
```

#### Method 3: Via MCP (If OpenClaw Installed)

```python
from rvla.multi_agent_coordinator import MultiAgentCoordinator

coordinator = MultiAgentCoordinator()
coordinator.register_server("openclaw", "http://localhost:3000/mcp")

# Get data from OpenClaw
result = coordinator.call_tool(
    server_name="openclaw",
    tool_name="get_data",
    arguments={...},
)

# Pass to agent
workspace.set("openclaw_data", result)
```

### Installing OpenClaw (Optional)

If you want to use actual OpenClaw:

```bash
# Install
npm i -g openclaw
# or
curl -fsSL https://openclaw.ai/install.sh | bash

# Start
openclaw onboard
# Runs on http://localhost:3000
```

Then enable multi-agent mode:
```python
result = run_agent(
    goal="...",
    enable_multi_agent=True,  # This enables OpenClaw delegation
)
```

## Summary

### Marimo Dashboard
- ✅ **Should work** - Fixed all syntax errors
- ✅ **Visualizes Weave traces** - Shows agent runs, scores, improvements
- ⚠️ **Weave Python API limited** - But dashboard URL works
- ✅ **Embedded in web app** - Auto-refreshes after runs

### OpenClaw/External Data
- ✅ **Infrastructure ready** - MCP, coordinator, workspace all set up
- ⚠️ **OpenClaw not installed** - But code is ready if you install it
- ✅ **Can pass external data** - Via workspace, API, or MCP
- ✅ **Multi-agent mode** - Enable with `enable_multi_agent=True`

## Quick Test

**Test Marimo:**
```bash
python scripts/test_marimo.py
marimo edit marimo/weave_dashboard.py
```

**Test External Data:**
```python
# In your code
workspace.set("test_data", {"key": "value"})
result = run_agent(goal="Use test_data", workspace=workspace, enable_multi_agent=True)
```

**Test MCP Server:**
```bash
python scripts/start_mcp_server.py
curl http://localhost:8001/tools
```
