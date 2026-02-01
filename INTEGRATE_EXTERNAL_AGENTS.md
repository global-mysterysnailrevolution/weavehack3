# Integrating External Agents and API Calls

## Overview

Your RLM-VLA agent can receive data from:
1. **OpenClaw** (if installed) - via MCP protocol
2. **External API calls** - via the agent's context/workspace
3. **Other agents** - via MCP or direct function calls

## Current Status

### ✅ What Works Now

1. **RLM-VLA Agent** - Fully functional, logs to Weave
2. **MCP Server** - Exposes agent tools to other agents
3. **Multi-Agent Coordinator** - Infrastructure ready for OpenClaw
4. **Workspace/Memory** - Can store external data
5. **Weave Tracing** - All operations traced

### ⚠️ OpenClaw Integration

**Important:** OpenClaw is NOT currently installed. The code has integration stubs, but you need to:

1. **Install OpenClaw** (if you want to use it):
   ```bash
   npm i -g openclaw
   # or
   curl -fsSL https://openclaw.ai/install.sh | bash
   ```

2. **Start OpenClaw Gateway**:
   ```bash
   openclaw onboard
   # Runs on http://localhost:3000 by default
   ```

3. **Enable Multi-Agent Mode**:
   ```python
   result = run_agent(
       goal="...",
       driver=driver,
       workspace=workspace,
       enable_multi_agent=True,  # This enables OpenClaw delegation
   )
   ```

## How to Pass Data from External Sources

### Method 1: Via Workspace (Memory)

The agent's workspace can store external data:

```python
from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver

workspace = workspace_from_env()
driver = WebDriver()

# Store external data in workspace
workspace.set("external_data", {
    "api_response": {...},
    "openclaw_result": {...},
    "user_input": "...",
})

# Agent can access this via events
result = run_agent(
    goal="Use the external data to complete task",
    driver=driver,
    workspace=workspace,
    enable_multi_agent=True,
)
```

### Method 2: Via MCP Tools

If you have OpenClaw or another MCP agent running:

```python
from rvla.multi_agent_coordinator import MultiAgentCoordinator
from rvla.mcp_tools import call_mcp_tool

# Call OpenClaw tool
coordinator = MultiAgentCoordinator()
coordinator.register_server("openclaw", "http://localhost:3000/mcp")

# Get data from OpenClaw
openclaw_result = coordinator.call_tool(
    server_name="openclaw",
    tool_name="get_file_contents",
    arguments={"path": "data.json"},
)

# Pass to agent via workspace
workspace.set("openclaw_data", openclaw_result)
```

### Method 3: Via API Endpoint

The `/api/openclaw/beach` and `/api/openclaw/sea` endpoints accept goals and can include context:

```python
# POST to /api/openclaw/beach
{
    "goal": "Task description",
    "iteration": 0,
    # You can extend OpenClawRequest to include external data
}
```

To add external data support, modify `api/main.py`:

```python
class OpenClawRequest(BaseModel):
    goal: str
    iteration: int = 0
    external_data: dict[str, Any] | None = None  # Add this
    context: dict[str, Any] | None = None  # Add this

# Then in _stream_openclaw:
if request.external_data:
    workspace.set("external_data", request.external_data)
if request.context:
    workspace.set("context", request.context)
```

### Method 4: Direct Function Calls

You can call the agent directly with pre-loaded data:

```python
from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver

workspace = workspace_from_env()

# Pre-populate workspace with external data
workspace.set("events", [
    "external_api_call: got data from API",
    "openclaw_result: file saved successfully",
    "user_input: process this data",
])

# Run agent - it will see the pre-loaded events
result = run_agent(
    goal="Process the external data",
    driver=driver,
    workspace=workspace,
    enable_multi_agent=True,
)
```

## Example: OpenClaw → RLM-VLA Flow

If you install OpenClaw, here's how data flows:

```
1. OpenClaw receives task: "Research pricing, save to file"
   ↓
2. OpenClaw calls RLM-VLA via MCP:
   POST http://localhost:8001/tools/call
   {
     "tool": "navigate_web",
     "arguments": {
       "url": "https://example.com/pricing",
       "goal": "Extract pricing data"
     }
   }
   ↓
3. RLM-VLA agent runs, extracts data
   ↓
4. RLM-VLA returns result to OpenClaw
   ↓
5. OpenClaw saves to file using its own tools
```

## Example: API Call → Agent Flow

```python
# External API call
import requests
api_data = requests.get("https://api.example.com/data").json()

# Pass to agent
workspace = workspace_from_env()
workspace.set("api_data", api_data)

result = run_agent(
    goal=f"Process this data: {api_data}",
    driver=driver,
    workspace=workspace,
)
```

## Testing Integration

### Test MCP Server

```bash
# Start your MCP server
python scripts/start_mcp_server.py

# In another terminal, test it
curl http://localhost:8001/tools
curl -X POST http://localhost:8001/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "navigate_web", "arguments": {"url": "https://example.com", "goal": "test"}}'
```

### Test OpenClaw Integration (if installed)

```python
from rvla.multi_agent_coordinator import MultiAgentCoordinator

coordinator = MultiAgentCoordinator()
coordinator.register_server("openclaw", "http://localhost:3000/mcp")

# List available tools
tools = coordinator.get_tools("openclaw")
print(f"OpenClaw tools: {tools}")

# Call a tool
result = coordinator.call_tool(
    server_name="openclaw",
    tool_name="save_file",
    arguments={"path": "test.txt", "content": "Hello"},
)
```

## Summary

✅ **Marimo Dashboard** - Should work, visualizes Weave traces  
✅ **Pass External Data** - Via workspace, MCP, API endpoints, or direct calls  
⚠️ **OpenClaw** - Code ready, but needs OpenClaw installed  
✅ **MCP Integration** - Fully functional, can receive calls from other agents  

The infrastructure is ready - you just need to:
1. Install OpenClaw (if desired)
2. Use workspace.set() to pass external data
3. Enable multi_agent=True when running the agent
