# RLM-VLA MCP Server

This is the MCP (Model Context Protocol) server that exposes your RLM-VLA agent's capabilities so other agents (OpenClaw, Gastown, etc.) can call it.

## Quick Start

```bash
# Start the MCP server
python scripts/start_mcp_server.py

# Server runs on http://localhost:8001 by default
```

## What It Does

Exposes your RLM-VLA agent as an MCP server with these tools:

1. **`navigate_web`** - Navigate to a URL and extract information
2. **`extract_data`** - Extract structured data from a webpage
3. **`multi_page_navigation`** - Navigate across multiple pages for complex tasks

## API Endpoints

- `GET /` - Server info
- `GET /health` - Health check
- `GET /tools` - List all available tools
- `POST /tools/call` - Call a tool
- `POST /register` - Register additional tools (extensibility)

## Usage from OpenClaw

1. **Start your MCP server:**
   ```bash
   python scripts/start_mcp_server.py
   ```

2. **Configure OpenClaw to use your server:**
   - Set `RLM_VLA_MCP_URL=http://localhost:8001` in OpenClaw config
   - Or add it as a custom MCP provider

3. **OpenClaw can now call your tools:**
   ```python
   # From OpenClaw
   result = await mcp.call("navigate_web", {
       "url": "https://example.com",
       "goal": "Extract pricing information"
   })
   ```

## Example: Multi-Agent Workflow

```
User → OpenClaw: "Research SaaS pricing, save to file"

OpenClaw:
  1. Calls RLM-VLA MCP: navigate_web("https://saas.com/pricing", "extract pricing")
  2. Receives extracted data
  3. Saves to file (OpenClaw's native capability)
  4. Sends email summary (OpenClaw's native capability)
```

## Configuration

Environment variables:
- `MCP_SERVER_PORT` - Port to run on (default: 8001)
- `MCP_SERVER_HOST` - Host to bind to (default: 0.0.0.0)
- `OPENAI_API_KEY` - Required for agent execution
- `WANDB_API_KEY` - For Weave tracing
- `REDIS_URL` - Optional, for external memory

## Testing

```bash
# Test the server
curl http://localhost:8001/tools

# Test a tool call
curl -X POST http://localhost:8001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "navigate_web",
    "arguments": {
      "url": "https://example.com",
      "goal": "Extract the main heading"
    }
  }'
```

## Architecture

```
┌─────────────┐
│  OpenClaw   │
│   Agent     │
└──────┬──────┘
       │ MCP Protocol
       │ (HTTP/REST)
       ▼
┌─────────────────┐
│  RLM-VLA MCP    │
│     Server      │
│  (this server)  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  RLM-VLA Agent  │
│  (your agent)   │
└─────────────────┘
```

## Why This Matters

- **Bidirectional**: Your agent can call OpenClaw, AND OpenClaw can call your agent
- **Standard Protocol**: Uses MCP, so any MCP-compatible agent can use it
- **Fully Traced**: All tool calls are traced to Weave
- **Extensible**: Easy to add new tools
