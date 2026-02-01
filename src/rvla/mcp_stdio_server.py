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
    import weave
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
        {
            "name": "weave_get_traces",
            "description": "Get recent Weave traces/runs. View all operations logged to Weave.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of traces to return (default: 20)",
                        "default": 20
                    },
                    "op_name_filter": {
                        "type": "string",
                        "description": "Filter traces by operation name (optional)"
                    }
                }
            }
        },
        {
            "name": "weave_get_dashboard_url",
            "description": "Get the Weave dashboard URL to view charts and visualizations in browser",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "weave_analyze_trace",
            "description": "Analyze a specific Weave trace by ID. Get detailed information about inputs, outputs, and execution.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "trace_id": {
                        "type": "string",
                        "description": "The trace/run ID to analyze"
                    }
                },
                "required": ["trace_id"]
            }
        },
        {
            "name": "weave_query_traces",
            "description": "Query Weave traces with filters. Find traces by operation name, date range, or other criteria.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "op_name": {
                        "type": "string",
                        "description": "Filter by operation name (e.g., 'record_openclaw_run', 'plan_next_action')"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results (default: 50)",
                        "default": 50
                    }
                }
            }
        },
        {
            "name": "weave_get_metrics",
            "description": "Get performance metrics from Weave traces. Analyze execution times, success rates, and trends.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "op_name": {
                        "type": "string",
                        "description": "Operation name to analyze (optional, analyzes all if not provided)"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Number of recent runs to analyze (default: 100)",
                        "default": 100
                    }
                }
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
    
    # W&B/Weave tools don't need driver/workspace
    if tool_name.startswith("weave_"):
        # Handle Weave tools (no driver needed)
        pass  # Will be handled below
    else:
        # Web navigation tools need driver/workspace
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
        
        elif tool_name == "weave_get_traces":
            limit = int(arguments.get("limit", 20))
            op_name_filter = arguments.get("op_name_filter")
            
            try:
                runs = list(weave.get_op_runs(limit=limit))
                
                traces = []
                for run in runs:
                    if op_name_filter and op_name_filter.lower() not in str(getattr(run, "op_name", "")).lower():
                        continue
                    
                    trace_info = {
                        "id": getattr(run, "id", None) or str(run)[:50],
                        "op_name": getattr(run, "op_name", "unknown"),
                        "started_at": str(getattr(run, "started_at", "")) if hasattr(run, "started_at") else None,
                        "duration": getattr(run, "duration", None),
                        "status": getattr(run, "status", "unknown"),
                    }
                    
                    # Try to get inputs/outputs if available
                    try:
                        if hasattr(run, "inputs"):
                            trace_info["inputs"] = str(run.inputs)[:200]
                        if hasattr(run, "output"):
                            trace_info["output"] = str(run.output)[:200]
                    except:
                        pass
                    
                    traces.append(trace_info)
                
                send_response(request_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "traces": traces,
                                "count": len(traces),
                                "limit": limit,
                                "filter": op_name_filter or "none"
                            }, indent=2)
                        }
                    ]
                })
            except Exception as e:
                send_response(request_id, error={
                    "code": -32000,
                    "message": f"Failed to get Weave traces: {str(e)}"
                })
        
        elif tool_name == "weave_get_dashboard_url":
            try:
                entity = os.getenv("WANDB_ENTITY", "")
                project = os.getenv("WANDB_PROJECT", "weavehacks-rvla")
                
                if entity:
                    url = f"https://wandb.ai/{entity}/{project}/weave"
                else:
                    url = f"https://wandb.ai/{project}/weave"
                
                send_response(request_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "dashboard_url": url,
                                "entity": entity or "not_set",
                                "project": project,
                                "instructions": "Open this URL in your browser to view Weave charts, traces, and visualizations"
                            }, indent=2)
                        }
                    ]
                })
            except Exception as e:
                send_response(request_id, error={
                    "code": -32000,
                    "message": f"Failed to get dashboard URL: {str(e)}"
                })
        
        elif tool_name == "weave_analyze_trace":
            trace_id = arguments.get("trace_id", "")
            
            try:
                # Get all runs and find the one matching trace_id
                runs = list(weave.get_op_runs(limit=1000))
                run = None
                for r in runs:
                    run_id = getattr(r, "id", None) or str(r)[:50]
                    if str(run_id) == str(trace_id) or str(trace_id) in str(run_id):
                        run = r
                        break
                
                if not run:
                    send_response(request_id, error={
                        "code": -32000,
                        "message": f"Trace not found: {trace_id}"
                    })
                    return
                
                analysis = {
                    "id": trace_id,
                    "op_name": getattr(run, "op_name", "unknown"),
                    "started_at": str(getattr(run, "started_at", "")) if hasattr(run, "started_at") else None,
                    "duration": getattr(run, "duration", None),
                    "status": getattr(run, "status", "unknown"),
                }
                
                # Get inputs
                try:
                    if hasattr(run, "inputs"):
                        analysis["inputs"] = run.inputs
                    elif hasattr(run, "get_inputs"):
                        analysis["inputs"] = run.get_inputs()
                except:
                    analysis["inputs"] = "Unable to retrieve"
                
                # Get output
                try:
                    if hasattr(run, "output"):
                        analysis["output"] = run.output
                    elif hasattr(run, "result"):
                        analysis["output"] = run.result
                    elif hasattr(run, "get_output"):
                        analysis["output"] = run.get_output()
                except:
                    analysis["output"] = "Unable to retrieve"
                
                send_response(request_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(analysis, indent=2, default=str)
                        }
                    ]
                })
            except Exception as e:
                send_response(request_id, error={
                    "code": -32000,
                    "message": f"Failed to analyze trace: {str(e)}"
                })
        
        elif tool_name == "weave_query_traces":
            op_name = arguments.get("op_name", "")
            limit = int(arguments.get("limit", 50))
            
            try:
                runs = list(weave.get_op_runs(limit=limit * 2))  # Get more to filter
                
                filtered = []
                for run in runs:
                    run_op_name = str(getattr(run, "op_name", ""))
                    if op_name and op_name.lower() not in run_op_name.lower():
                        continue
                    
                    filtered.append({
                        "id": getattr(run, "id", None) or str(run)[:50],
                        "op_name": run_op_name,
                        "started_at": str(getattr(run, "started_at", "")) if hasattr(run, "started_at") else None,
                        "duration": getattr(run, "duration", None),
                        "status": getattr(run, "status", "unknown"),
                    })
                    
                    if len(filtered) >= limit:
                        break
                
                send_response(request_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "traces": filtered,
                                "count": len(filtered),
                                "filter": op_name or "none",
                                "limit": limit
                            }, indent=2)
                        }
                    ]
                })
            except Exception as e:
                send_response(request_id, error={
                    "code": -32000,
                    "message": f"Failed to query traces: {str(e)}"
                })
        
        elif tool_name == "weave_get_metrics":
            op_name = arguments.get("op_name")
            limit = int(arguments.get("limit", 100))
            
            try:
                runs = list(weave.get_op_runs(limit=limit))
                
                if op_name:
                    runs = [r for r in runs if op_name.lower() in str(getattr(r, "op_name", "")).lower()]
                
                metrics = {
                    "total_runs": len(runs),
                    "op_name_filter": op_name or "all",
                    "success_count": 0,
                    "failed_count": 0,
                    "total_duration": 0.0,
                    "avg_duration": 0.0,
                    "operations": {}
                }
                
                for run in runs:
                    run_op_name = str(getattr(run, "op_name", "unknown"))
                    status = str(getattr(run, "status", "unknown")).lower()
                    duration = getattr(run, "duration", 0) or 0
                    
                    if status in ["success", "completed", "ok"]:
                        metrics["success_count"] += 1
                    elif status in ["error", "failed", "exception"]:
                        metrics["failed_count"] += 1
                    
                    metrics["total_duration"] += float(duration) if duration else 0.0
                    
                    if run_op_name not in metrics["operations"]:
                        metrics["operations"][run_op_name] = {
                            "count": 0,
                            "total_duration": 0.0,
                            "success_count": 0,
                            "failed_count": 0
                        }
                    
                    metrics["operations"][run_op_name]["count"] += 1
                    metrics["operations"][run_op_name]["total_duration"] += float(duration) if duration else 0.0
                    if status in ["success", "completed", "ok"]:
                        metrics["operations"][run_op_name]["success_count"] += 1
                    elif status in ["error", "failed", "exception"]:
                        metrics["operations"][run_op_name]["failed_count"] += 1
                
                if metrics["total_runs"] > 0:
                    metrics["avg_duration"] = metrics["total_duration"] / metrics["total_runs"]
                    metrics["success_rate"] = metrics["success_count"] / metrics["total_runs"]
                
                # Calculate averages for each operation
                for op_name_key, op_metrics in metrics["operations"].items():
                    if op_metrics["count"] > 0:
                        op_metrics["avg_duration"] = op_metrics["total_duration"] / op_metrics["count"]
                        op_metrics["success_rate"] = op_metrics["success_count"] / op_metrics["count"]
                
                send_response(request_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(metrics, indent=2, default=str)
                        }
                    ]
                })
            except Exception as e:
                send_response(request_id, error={
                    "code": -32000,
                    "message": f"Failed to get metrics: {str(e)}"
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
        # Only close driver if it was initialized (web tools)
        if not tool_name.startswith("weave_") and 'driver' in locals():
            try:
                driver.close()
            except:
                pass


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
            if not line or not line.strip():
                continue
            request = json.loads(line.strip())
            
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
