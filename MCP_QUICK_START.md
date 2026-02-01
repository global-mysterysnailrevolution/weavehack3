# MCP Server Quick Start

## Where Is Your MCP Server?

**Location**: `src/rvla/mcp_server.py`

**Start Script**: `scripts/start_mcp_server.py`

**Default Port**: `8001`

## How to Start It

```bash
# In one terminal, start the MCP server
python scripts/start_mcp_server.py

# Server will be available at:
# http://localhost:8001
```

## Verify It's Running

```bash
# Test the server
python scripts/test_mcp_server.py

# Or manually:
curl http://localhost:8001/health
curl http://localhost:8001/tools
```

## What Tools Does It Expose?

Your MCP server exposes 3 tools:

1. **`navigate_web(url, goal)`** - Navigate to URL and extract info
2. **`extract_data(url, data_type)`** - Extract structured data
3. **`multi_page_navigation(task, pages)`** - Complex multi-page tasks

## How OpenClaw Can Use It

1. **Start your MCP server:**
   ```bash
   python scripts/start_mcp_server.py
   ```

2. **In OpenClaw, configure MCP provider:**
   - URL: `http://localhost:8001`
   - Or set environment variable: `RLM_VLA_MCP_URL=http://localhost:8001`

3. **OpenClaw can now call your tools:**
   ```python
   # From OpenClaw skill or agent
   result = await mcp.call("navigate_web", {
       "url": "https://example.com",
       "goal": "Extract pricing table"
   })
   ```

## Architecture

```
┌─────────────┐
│  OpenClaw   │  ← Can call your agent
└──────┬──────┘
       │ MCP
       ▼
┌─────────────────┐
│  Your MCP       │  ← src/rvla/mcp_server.py
│  Server         │
│  (port 8001)    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  RLM-VLA Agent  │  ← Your agent code
└─────────────────┘
```

## Current Status

✅ **MCP Server**: Implemented (`src/rvla/mcp_server.py`)
✅ **Start Script**: Ready (`scripts/start_mcp_server.py`)
✅ **Test Script**: Ready (`scripts/test_mcp_server.py`)
✅ **Documentation**: Complete

## Next Steps

1. **Start the server**: `python scripts/start_mcp_server.py`
2. **Test it**: `python scripts/test_mcp_server.py`
3. **Configure OpenClaw** to use `http://localhost:8001`
4. **Try a multi-agent workflow**!

## Troubleshooting

**Server won't start?**
- Check if port 8001 is already in use
- Set `MCP_SERVER_PORT=8002` to use different port

**OpenClaw can't connect?**
- Make sure server is running: `curl http://localhost:8001/health`
- Check firewall/network settings
- Verify OpenClaw config has correct URL

**Tools not working?**
- Check `OPENAI_API_KEY` is set
- Check `WANDB_API_KEY` is set (for tracing)
- Look at server logs for errors
