"""MCP (Model Context Protocol) tools for agent coordination.

MCP allows agents to expose capabilities and communicate.
"""

from __future__ import annotations

import os
from typing import Any
import httpx

import weave

# Ensure Weave is initialized
from rvla.weave_init import ensure_weave_init
ensure_weave_init()


@weave.op()
def call_mcp_tool(
    mcp_server_url: str,
    tool_name: str,
    arguments: dict[str, Any],
    api_key: str | None = None,
) -> dict[str, Any]:
    """Call an MCP tool from another agent."""
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "tool": tool_name,
            "arguments": arguments,
        }
        
        response = httpx.post(
            f"{mcp_server_url}/tools/call",
            json=payload,
            headers=headers,
            timeout=30,
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"MCP returned {response.status_code}"}
            
    except Exception as e:
        return {"error": str(e)}


@weave.op()
def list_mcp_tools(
    mcp_server_url: str,
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    """List available tools from an MCP server."""
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = httpx.get(
            f"{mcp_server_url}/tools",
            headers=headers,
            timeout=10,
        )
        
        if response.status_code == 200:
            return response.json().get("tools", [])
        else:
            return []
            
    except Exception as e:
        print(f"[WARN] Failed to list MCP tools: {e}")
        return []


@weave.op()
def register_rlm_vla_tools(
    mcp_server_url: str,
) -> dict[str, Any]:
    """Register RLM-VLA agent tools as MCP server.
    
    This allows other agents (OpenClaw, Gastown) to call our agent.
    """
    tools = [
        {
            "name": "navigate_web",
            "description": "Navigate to a URL and extract information",
            "parameters": {
                "url": {"type": "string", "description": "URL to navigate to"},
                "goal": {"type": "string", "description": "What to extract/find"},
            }
        },
        {
            "name": "extract_data",
            "description": "Extract structured data from a webpage",
            "parameters": {
                "url": {"type": "string"},
                "data_type": {"type": "string", "description": "Type of data to extract"},
            }
        },
        {
            "name": "multi_page_navigation",
            "description": "Navigate across multiple pages to complete a task",
            "parameters": {
                "task": {"type": "string"},
                "pages": {"type": "array", "items": {"type": "string"}},
            }
        },
    ]
    
    try:
        response = httpx.post(
            f"{mcp_server_url}/register",
            json={"tools": tools, "agent": "rlm_vla"},
            timeout=10,
        )
        
        if response.status_code == 200:
            return {"status": "registered", "tools": len(tools)}
        else:
            return {"error": f"Registration failed: {response.status_code}"}
            
    except Exception as e:
        return {"error": str(e)}


class MCPCoordinator:
    """Manages MCP connections for multi-agent coordination."""
    
    def __init__(self):
        self.registered_servers: dict[str, str] = {}  # name -> url
    
    def register_server(
        self,
        name: str,
        url: str,
        api_key: str | None = None,
    ) -> None:
        """Register an MCP server."""
        self.registered_servers[name] = url
        if api_key:
            os.environ[f"MCP_{name.upper()}_API_KEY"] = api_key
    
    def get_tools(self, server_name: str) -> list[dict[str, Any]]:
        """Get available tools from a registered MCP server."""
        if server_name not in self.registered_servers:
            return []
        
        return list_mcp_tools(
            self.registered_servers[server_name],
            api_key=os.getenv(f"MCP_{server_name.upper()}_API_KEY"),
        )
    
    def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Call a tool on a registered MCP server."""
        if server_name not in self.registered_servers:
            return {"error": f"Server {server_name} not registered"}
        
        return call_mcp_tool(
            mcp_server_url=self.registered_servers[server_name],
            tool_name=tool_name,
            arguments=arguments,
            api_key=os.getenv(f"MCP_{server_name.upper()}_API_KEY"),
        )
