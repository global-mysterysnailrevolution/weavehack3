# Setting Up MCP Server in Cursor

## The Problem

Cursor expects MCP servers to use **stdio protocol** (standard input/output), not REST API. We've created both:
- REST API server (`mcp_server.py`) - for OpenClaw/other agents
- **stdio server** (`mcp_stdio_server.py`) - **for Cursor**

## Quick Setup

### Step 1: Add to Cursor Settings

Open Cursor Settings (Ctrl+,) and search for "MCP" or go to:
- **Settings → Features → MCP Servers**

Or manually edit your Cursor settings JSON:
- Press `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"
- Add this configuration:

```json
{
  "mcpServers": {
    "rlm-vla": {
      "command": "python",
      "args": [
        "-m",
        "rvla.mcp_stdio_server"
      ],
      "cwd": "${workspaceFolder}",
      "env": {
        "OPENAI_API_KEY": "${env:OPENAI_API_KEY}",
        "WANDB_API_KEY": "${env:WANDB_API_KEY}",
        "WANDB_PROJECT": "${env:WANDB_PROJECT}",
        "WANDB_ENTITY": "${env:WANDB_ENTITY}"
      }
    }
  }
}
```

### Step 2: Restart Cursor

After adding the configuration, **restart Cursor completely**.

### Step 3: Verify

1. Open Cursor
2. Go to **Settings → Features → MCP Servers**
3. You should see **"rlm-vla"** in the list
4. It should show as "Connected" or "Ready"

## Alternative: Settings File Location

If the UI doesn't work, edit the settings file directly:

**Windows:**
```
%APPDATA%\Cursor\User\settings.json
```

**Mac:**
```
~/Library/Application Support/Cursor/User/settings.json
```

**Linux:**
```
~/.config/Cursor/User/settings.json
```

Add the `mcpServers` section to your settings.json.

## What Tools Will Be Available

Once configured, you'll have 3 tools available in Cursor:

1. **`navigate_web`** - Navigate to URL and extract info
2. **`extract_data`** - Extract structured data from webpage
3. **`multi_page_navigation`** - Complex multi-page navigation

## Troubleshooting

**Not showing up?**
- Make sure `pip install -e .` was run (package is installed)
- Check that `rvla.mcp_stdio_server` module exists
- Restart Cursor completely
- Check Cursor's output/logs for errors

**Connection errors?**
- Verify environment variables are set
- Check that Python is in PATH
- Look at Cursor's developer console for errors

**Tools not working?**
- Make sure `OPENAI_API_KEY` is set
- Check that `WANDB_API_KEY` is set (for tracing)
- Verify the workspace folder is correct

## Testing

Once it's set up, you can test it by:
1. Opening Cursor's MCP tools panel
2. Trying to use one of the tools
3. Or checking the MCP server status in settings

---

**The stdio server is ready at `src/rvla/mcp_stdio_server.py`** - you just need to configure Cursor to use it!
