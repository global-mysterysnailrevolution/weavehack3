# How to Start Your MCP Server in Cursor

## ✅ Everything is Ready!

Your MCP server is set up and ready to run. Here's how to start it:

## Quick Start

### Option 1: Run in Cursor Terminal

Open a terminal in Cursor and run:

```bash
python scripts/start_mcp_server.py
```

The server will start on **http://localhost:8001**

### Option 2: Run as Background Process

In Cursor, you can also run it in the background, but it's easier to use a separate terminal window.

## Verify It's Running

Once started, test it:

```bash
# In another terminal
python scripts/test_mcp_server.py

# Or manually:
curl http://localhost:8001/health
curl http://localhost:8001/tools
```

## What You'll See

When the server starts, you'll see:

```
======================================================================
RLM-VLA MCP Server
======================================================================
Starting server on 0.0.0.0:8001
MCP endpoint: http://0.0.0.0:8001
Tools endpoint: http://0.0.0.0:8001/tools
Call endpoint: http://0.0.0.0:8001/tools/call
======================================================================
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

## Available Endpoints

- **Health**: `http://localhost:8001/health`
- **List Tools**: `http://localhost:8001/tools`
- **Call Tool**: `POST http://localhost:8001/tools/call`

## Exposed Tools

Your server exposes 3 tools:

1. **`navigate_web(url, goal)`** - Navigate to URL and extract info
2. **`extract_data(url, data_type)`** - Extract structured data
3. **`multi_page_navigation(task, pages)`** - Complex multi-page tasks

## Use with OpenClaw

Once running, configure OpenClaw to use:
- **MCP Server URL**: `http://localhost:8001`

OpenClaw can then call your agent's tools via MCP!

## Files Created

- ✅ `src/rvla/mcp_server.py` - Main MCP server
- ✅ `scripts/start_mcp_server.py` - Startup script
- ✅ `scripts/test_mcp_server.py` - Test script
- ✅ `MCP_QUICK_START.md` - Quick reference
- ✅ `MCP_SERVER_README.md` - Full documentation

## Troubleshooting

**Port already in use?**
```bash
# Use a different port
MCP_SERVER_PORT=8002 python scripts/start_mcp_server.py
```

**Module not found?**
```bash
# Install the package
pip install -e .
```

**Server won't start?**
- Check that `OPENAI_API_KEY` is set
- Check that `WANDB_API_KEY` is set (for tracing)
- Look at the error message in the terminal

## Next Steps

1. **Start the server**: `python scripts/start_mcp_server.py`
2. **Test it**: `python scripts/test_mcp_server.py` (in another terminal)
3. **Configure OpenClaw** to use `http://localhost:8001`
4. **Try a multi-agent workflow!**

---

**Your MCP server is ready to go!** 🚀
