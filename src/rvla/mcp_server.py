"""MCP Server for RLM-VLA Agent.

This exposes the RLM-VLA agent's capabilities as an MCP server
so other agents (OpenClaw, Gastown) can call it.
"""

from __future__ import annotations

import os
import json
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Ensure Weave is initialized
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver

app = FastAPI(title="RLM-VLA MCP Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ToolCallRequest(BaseModel):
    tool: str
    arguments: dict[str, Any]


class ToolRegistrationRequest(BaseModel):
    tools: list[dict[str, Any]]
    agent: str


# Store registered tools (in production, use Redis or DB)
_registered_tools: list[dict[str, Any]] = []


@app.get("/")
async def root():
    return {
        "name": "RLM-VLA MCP Server",
        "version": "0.1.0",
        "status": "running",
        "tools": len(_registered_tools),
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/tools")
async def list_tools():
    """List all available MCP tools."""
    # Return our built-in tools + any registered tools
    builtin_tools = [
        {
            "name": "navigate_web",
            "description": "Navigate to a URL and extract information using RLM-VLA agent",
            "parameters": {
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
            "parameters": {
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
            "parameters": {
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
    
    return {
        "tools": builtin_tools + _registered_tools,
        "total": len(builtin_tools) + len(_registered_tools),
    }


@app.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    """Call an MCP tool."""
    tool_name = request.tool
    arguments = request.arguments
    
    # Initialize components
    workspace = workspace_from_env()
    driver = WebDriver()
    
    try:
        if tool_name == "navigate_web":
            url = arguments.get("url", "")
            goal = arguments.get("goal", f"Navigate to {url} and extract information")
            
            full_goal = f"{goal}. Start by navigating to {url}."
            
            result = run_agent(
                goal=full_goal,
                driver=driver,
                workspace=workspace,
                enable_multi_agent=False,
            )
            
            return {
                "tool": tool_name,
                "success": True,
                "result": {
                    "url": result.get("last_observation", {}).url if result.get("last_observation") else url,
                    "steps": len(result.get("trajectory", [])),
                    "events": result.get("events", [])[-10:],  # Last 10 events
                    "score": result.get("score", {}),
                }
            }
        
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
            
            # Extract relevant events that might contain data
            extraction_events = [
                e for e in result.get("events", [])
                if "extract" in e.lower() or "data" in e.lower() or "pricing" in e.lower()
            ]
            
            return {
                "tool": tool_name,
                "success": True,
                "result": {
                    "url": url,
                    "data_type": data_type,
                    "extracted_data": extraction_events[-5:] if extraction_events else [],
                    "steps": len(result.get("trajectory", [])),
                }
            }
        
        elif tool_name == "multi_page_navigation":
            task = arguments.get("task", "")
            pages = arguments.get("pages", [])
            
            goal = f"{task}. Navigate through these pages: {', '.join(pages)}"
            
            result = run_agent(
                goal=goal,
                driver=driver,
                workspace=workspace,
                enable_multi_agent=True,  # Enable multi-agent for complex tasks
            )
            
            return {
                "tool": tool_name,
                "success": True,
                "result": {
                    "task": task,
                    "pages_visited": len(pages),
                    "steps": len(result.get("trajectory", [])),
                    "events": result.get("events", [])[-20:],
                    "score": result.get("score", {}),
                }
            }
        
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown tool: {tool_name}. Available tools: navigate_web, extract_data, multi_page_navigation"
            )
    
    except Exception as e:
        return {
            "tool": tool_name,
            "success": False,
            "error": str(e),
        }
    
    finally:
        driver.close()


@app.post("/register")
async def register_tools(request: ToolRegistrationRequest):
    """Register additional tools (for extensibility)."""
    global _registered_tools
    
    _registered_tools.extend(request.tools)
    
    return {
        "status": "registered",
        "agent": request.agent,
        "tools_registered": len(request.tools),
        "total_tools": len(_registered_tools),
    }


def main():
    """Run the MCP server."""
    port = int(os.getenv("MCP_SERVER_PORT", 8001))
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    
    print("="*70)
    print("RLM-VLA MCP Server")
    print("="*70)
    print(f"Starting server on {host}:{port}")
    print(f"MCP endpoint: http://{host}:{port}")
    print(f"Tools endpoint: http://{host}:{port}/tools")
    print(f"Call endpoint: http://{host}:{port}/tools/call")
    print("="*70)
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
