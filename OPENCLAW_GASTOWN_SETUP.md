# OpenClaw & Gastown Integration Setup

## Quick Setup Guide

### 1. Install OpenClaw

```bash
# One-liner install (from https://openclaw.ai/)
curl -fsSL https://openclaw.ai/install.sh | bash

# Or via npm
npm i -g openclaw

# Start OpenClaw
openclaw onboard
```

OpenClaw will run on `http://localhost:3000` by default.

### 2. Setup Gastown (if using)

Gastown is a multi-agent coordination framework. Check the [GitHub repo](https://github.com/steveyegge/gastown) for setup instructions.

### 3. Configure Environment

Add to your `.env`:

```bash
# OpenClaw MCP Server
OPENCLAW_MCP_URL=http://localhost:3000/mcp
OPENCLAW_API_KEY=your_key_if_needed

# Gastown
GASTOWN_MCP_URL=http://localhost:8080/mcp
GASTOWN_API_KEY=your_key_if_needed
```

### 4. Use in Your Agent

```python
from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver

# Enable multi-agent coordination
result = run_agent(
    goal="Navigate web, extract data, save to file",
    driver=WebDriver(),
    workspace=workspace_from_env(),
    enable_multi_agent=True,  # Enable coordination
)
```

## How It Works

### RLM-VLA Agent Responsibilities:
- ✅ Web navigation (complex multi-page)
- ✅ Visual analysis (screenshots)
- ✅ Data extraction
- ✅ RLM context examination

### OpenClaw Responsibilities:
- ✅ File operations (save, organize)
- ✅ Calendar management
- ✅ Email sending
- ✅ System commands
- ✅ Local file access

### Gastown Responsibilities:
- ✅ Workflow orchestration
- ✅ Task delegation
- ✅ Error handling
- ✅ Multi-agent coordination

## Example Workflow

```
User: "Research SaaS pricing, save to file, email me summary"

1. RLM-VLA Agent:
   - Navigates to 3 SaaS sites
   - Extracts pricing data
   - Uses RLM to handle long context

2. OpenClaw (via MCP):
   - Receives extracted data
   - Saves to organized file structure
   - Sends email summary via WhatsApp/Telegram

3. Gastown (optional):
   - Coordinates the workflow
   - Handles errors
   - Manages retries
```

## MCP Tools We Expose

Our RLM-VLA agent exposes these MCP tools for other agents to use:

- `navigate_web(url, goal)` - Navigate and extract
- `extract_data(url, data_type)` - Extract structured data  
- `multi_page_navigation(task, pages)` - Complex navigation

## OpenClaw Skills

You can also create OpenClaw skills that call our agent:

```javascript
// Example OpenClaw skill
{
  name: "web_research",
  description: "Research web and extract data",
  handler: async (task) => {
    // Call RLM-VLA agent via MCP
    return await mcp.call("navigate_web", {
      url: task.url,
      goal: task.goal,
    });
  }
}
```

## Testing

```python
# Test multi-agent coordination
python examples/multi_agent_demo.py
```

## Benefits

1. **Division of Labor**: Each agent does what it's best at
2. **Scalability**: Multiple agents working in parallel
3. **Flexibility**: Easy to add new agents via MCP
4. **Observability**: All operations traced in Weave
5. **Self-Improvement**: Learn from multi-agent traces
