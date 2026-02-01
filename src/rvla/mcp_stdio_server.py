"""MCP Server for RLM-VLA Agent using stdio protocol.

This implements the MCP (Model Context Protocol) stdio server
that Cursor can discover and use.
"""

from __future__ import annotations

import json
import sys
import os
from typing import Any
from contextlib import redirect_stdout, redirect_stderr
import io

# MCP stdio protocol: ONLY JSON-RPC on stdout, everything else to stderr
# Capture and suppress all output during imports (Weave prints to stdout)
_stdout_capture = io.StringIO()
_stderr_capture = io.StringIO()

with redirect_stdout(_stdout_capture), redirect_stderr(_stderr_capture):
    # Set environment variable to tell weave_init to be quiet
    os.environ['WEAVE_QUIET'] = '1'
    
    from rvla.weave_init import ensure_weave_init
    # Initialize Weave (output captured, won't break MCP protocol)
    ensure_weave_init()

# Now import the rest (also capture their stdout)
with redirect_stdout(_stdout_capture), redirect_stderr(_stderr_capture):
    from rvla.agent import run_agent
    from rvla.memory import workspace_from_env
    from rvla.web import WebDriver


def send_response(request_id: str | int | None, result: dict[str, Any] | None = None, error: dict[str, Any] | None = None):
    """Send a JSON-RPC response to stdout (MCP protocol)."""
    if request_id is None:
        # Can't send a response without an id - this is a programming error
        return
    
    response: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": request_id,
    }
    
    if error:
        response["error"] = error
    else:
        response["result"] = result if result is not None else {}
    
    # Write to stdout (MCP protocol requires JSON-RPC on stdout only)
    print(json.dumps(response), file=sys.stdout, flush=True)


def handle_initialize(params: dict[str, Any], request_id: str | int):
    """Handle initialize request."""
    send_response(request_id, {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "rlm-vla",
            "version": "0.1.0"
        }
    })


def handle_tools_list(params: dict[str, Any], request_id: str | int):
    """Handle tools/list request."""
    tools = [
        {
            "name": "navigate_web",
            "description": "Navigate to a URL and extract information using RLM-VLA agent",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to navigate to"
                    },
                    "goal": {
                        "type": "string",
                        "description": "What to extract or find on the page"
                    }
                },
                "required": ["url", "goal"]
            }
        },
        {
            "name": "extract_data",
            "description": "Extract structured data from a webpage",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the webpage"
                    },
                    "data_type": {
                        "type": "string",
                        "description": "Type of data to extract (e.g., 'pricing_table', 'product_info', 'contact_info')"
                    }
                },
                "required": ["url", "data_type"]
            }
        },
        {
            "name": "multi_page_navigation",
            "description": "Navigate across multiple pages to complete a complex task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The overall task to accomplish"
                    },
                    "pages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of URLs or page descriptions to navigate"
                    }
                },
                "required": ["task", "pages"]
            }
        },
    ]
    
    send_response(request_id, {"tools": tools})


def handle_tools_call(tool_name: str, arguments: dict[str, Any], request_id: str | int):
    """Handle tools/call request."""
    try:
        workspace = workspace_from_env()
    except Exception as e:
        send_response(request_id, error={
            "code": -32000,
            "message": f"Failed to initialize workspace: {str(e)}"
        })
        return
    
    try:
        driver = WebDriver()
    except Exception as e:
        send_response(request_id, error={
            "code": -32000,
            "message": f"Failed to initialize WebDriver: {str(e)}"
        })
        return
    
    try:
        if tool_name == "navigate_web":
            url = arguments.get("url", "")
            goal = arguments.get("goal", f"Navigate to {url} and extract information")
            
            full_goal = f"{goal}. Start by navigating to {url}."
            
            try:
                result = run_agent(
                    goal=full_goal,
                    driver=driver,
                    workspace=workspace,
                    enable_multi_agent=False,
                )
            except TypeError as e:
                if "proxies" in str(e):
                    # Browserbase/httpx compatibility issue - provide helpful error
                    send_response(request_id, error={
                        "code": -32000,
                        "message": f"Browserbase compatibility error: {str(e)}. Please check Browserbase and httpx versions are compatible."
                    })
                    return
                raise
            
            send_response(request_id, {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "url": result.get("last_observation", {}).url if result.get("last_observation") else url,
                            "steps": len(result.get("trajectory", [])),
                            "events": result.get("events", [])[-10:],
                            "score": result.get("score", {}),
                        }, indent=2)
                    }
                ]
            })
        
        elif tool_name == "extract_data":
            url = arguments.get("url", "")
            data_type = arguments.get("data_type", "general")
            
            goal = f"Navigate to {url} and extract {data_type} data from the page"
            
            result = run_agent(
                goal=goal,
                driver=driver,
                workspace=workspace,
                enable_multi_agent=False,
            )
            
            extraction_events = [
                e for e in result.get("events", [])
                if "extract" in e.lower() or "data" in e.lower() or "pricing" in e.lower()
            ]
            
            send_response(request_id, {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "url": url,
                            "data_type": data_type,
                            "extracted_data": extraction_events[-5:] if extraction_events else [],
                            "steps": len(result.get("trajectory", [])),
                        }, indent=2)
                    }
                ]
            })
        
        elif tool_name == "multi_page_navigation":
            task = arguments.get("task", "")
            pages = arguments.get("pages", [])
            
            goal = f"{task}. Navigate through these pages: {', '.join(pages)}"
            
            result = run_agent(
                goal=goal,
                driver=driver,
                workspace=workspace,
                enable_multi_agent=True,
            )
            
            send_response(request_id, {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "task": task,
                            "pages_visited": len(pages),
                            "steps": len(result.get("trajectory", [])),
                            "events": result.get("events", [])[-20:],
                            "score": result.get("score", {}),
                        }, indent=2)
                    }
                ]
            })
        
        else:
            send_response(request_id, error={
                "code": -32601,
                "message": f"Unknown tool: {tool_name}"
            })
    
    except Exception as e:
        send_response(request_id, error={
            "code": -32000,
            "message": str(e)
        })
    
    finally:
        driver.close()


def main():
    """Main MCP server loop using stdio."""
    # MCP stdio protocol: stdout is ONLY for JSON-RPC, stderr for everything else
    # Ensure any accidental stdout writes go to stderr (except our explicit JSON-RPC)
    # We already captured Weave output during import, but be extra safe
    
    initialized = False
    
    # Read requests from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue  # Skip empty lines
        
        try:
            request = json.loads(line)
            
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                handle_initialize(params, request_id)
                initialized = True
                # Send initialized notification after initialize response
                # Notifications don't have "id" or "result"
                notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                print(json.dumps(notification), file=sys.stdout, flush=True)
            elif method == "tools/list":
                handle_tools_list(params, request_id)
            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                handle_tools_call(tool_name, arguments, request_id)
            else:
                send_response(request_id, error={
                    "code": -32601,
                    "message": f"Unknown method: {method}"
                })
        
        except json.JSONDecodeError:
            continue
        except Exception as e:
            # If we have a request_id, send error response, otherwise skip
            if request_id is not None:
                send_response(request_id, error={
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                })


if __name__ == "__main__":
    main()
