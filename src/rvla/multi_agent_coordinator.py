"""Multi-agent coordinator for RLM-VLA agent working with OpenClaw, Gastown, and other agents.

Uses MCP (Model Context Protocol) and skills to coordinate between agents.
"""

from __future__ import annotations

import os
import json
from typing import Any
from dataclasses import dataclass
from enum import Enum

import weave

# Ensure Weave is initialized
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

import httpx


class AgentType(Enum):
    """Types of agents we can coordinate with."""
    OPENCLAW = "openclaw"
    GASTOWN = "gastown"
    RLM_VLA = "rlm_vla"  # Our agent
    CUSTOM = "custom"


@dataclass
class AgentTask:
    """A task to delegate to another agent."""
    agent_type: AgentType
    task: str
    context: dict[str, Any]
    priority: int = 5  # 1-10, higher = more urgent
    timeout: int = 300  # seconds


@dataclass
class AgentCapability:
    """Capabilities of an agent."""
    agent_type: AgentType
    capabilities: list[str]  # e.g., ["file_operations", "calendar", "email"]
    mcp_server_url: str | None = None
    skill_name: str | None = None


@weave.op()
def delegate_to_openclaw(
    task: str,
    context: dict[str, Any],
    gateway_url: str = "ws://127.0.0.1:18789",
) -> dict[str, Any]:
    """Delegate a task to OpenClaw agent via Gateway WebSocket or ACP.
    
    OpenClaw uses:
    - Gateway WebSocket on port 18789 (default)
    - ACP (Agent Control Protocol) for agent communication
    - Skills system for extensibility
    
    OpenClaw can:
    - File operations
    - Calendar management
    - Email sending
    - System commands
    - Browser control
    - And more via skills
    """
    try:
        import subprocess
        import json as json_lib
        
        # Method 1: Use OpenClaw CLI to send message/task
        # OpenClaw can receive tasks via CLI: openclaw agent --message "task"
        
        # Build task message
        task_message = f"Task from RLM-VLA agent: {task}"
        if context:
            task_message += f"\nContext: {json_lib.dumps(context, indent=2)}"
        
        # Try to send via OpenClaw CLI
        # Note: This requires OpenClaw gateway to be running
        # Try multiple possible CLI paths
        cli_paths = ["openclaw", "npx", "openclaw"]
        
        for cli_cmd in cli_paths:
            try:
                if cli_cmd == "npx":
                    cmd = ["npx", "-y", "openclaw", "agent", "--message", task_message, "--json"]
                else:
                    cmd = [cli_cmd, "agent", "--message", task_message, "--json"]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    shell=True,  # Use shell on Windows
                    encoding='utf-8',
                    errors='replace',  # Handle encoding errors gracefully
                )
                
                if result.returncode == 0:
                    try:
                        return json_lib.loads(result.stdout)
                    except:
                        return {"status": "sent", "output": result.stdout[:200]}
                elif "gateway" in result.stderr.lower() or "connection" in result.stderr.lower():
                    # Gateway not running - continue to next method
                    break
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                return {"error": "OpenClaw timeout", "fallback": "task_not_delegated"}
            except Exception:
                continue
        
        # Method 2: Try WebSocket connection to gateway
        # OpenClaw gateway uses WebSocket on port 18789
        try:
            import websocket
            ws = websocket.create_connection(gateway_url.replace("http://", "ws://").replace("https://", "wss://"))
            
            message = {
                "type": "task",
                "task": task,
                "context": context,
                "source": "rlm_vla",
            }
            
            ws.send(json_lib.dumps(message))
            response = ws.recv()
            ws.close()
            
            return json_lib.loads(response)
        except Exception as ws_error:
            return {
                "error": f"WebSocket failed: {str(ws_error)[:100]}",
                "fallback": "task_not_delegated",
                "note": "OpenClaw gateway may not be running. Try: openclaw gateway"
            }
            
    except Exception as e:
        return {"error": str(e), "fallback": "task_not_delegated"}


@weave.op()
def delegate_to_gastown(
    task: str,
    context: dict[str, Any],
    gastown_api_url: str = "http://localhost:8080",
) -> dict[str, Any]:
    """Delegate a task to Gastown agent.
    
    Gastown is a multi-agent coordination framework.
    """
    try:
        payload = {
            "task": task,
            "context": context,
            "agent_type": "rlm_vla",
        }
        
        response = httpx.post(
            f"{gastown_api_url}/delegate",
            json=payload,
            timeout=30,
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Gastown returned {response.status_code}"}
            
    except Exception as e:
        return {"error": str(e), "fallback": "task_not_delegated"}


@weave.op()
def discover_agent_capabilities(
    agent_type: AgentType,
) -> AgentCapability:
    """Discover what an agent can do via MCP or API."""
    if agent_type == AgentType.OPENCLAW:
        # OpenClaw capabilities (from their docs)
        return AgentCapability(
            agent_type=AgentType.OPENCLAW,
            capabilities=[
                "file_operations",
                "calendar_management",
                "email_sending",
                "system_commands",
                "browser_control",
                "web_scraping",
                "skill_execution",
            ],
            mcp_server_url=os.getenv("OPENCLAW_MCP_URL", "http://localhost:3000/mcp"),
        )
    
    elif agent_type == AgentType.GASTOWN:
        return AgentCapability(
            agent_type=AgentType.GASTOWN,
            capabilities=[
                "multi_agent_coordination",
                "task_delegation",
                "workflow_orchestration",
            ],
            mcp_server_url=os.getenv("GASTOWN_MCP_URL", "http://localhost:8080/mcp"),
        )
    
    else:
        return AgentCapability(
            agent_type=agent_type,
            capabilities=[],
        )


@weave.op()
def route_task_to_agent(
    task: str,
    required_capabilities: list[str],
    available_agents: list[AgentCapability],
) -> AgentType | None:
    """Route a task to the best agent based on capabilities."""
    # Score each agent
    best_agent = None
    best_score = 0
    
    for agent in available_agents:
        score = sum(1 for cap in required_capabilities if cap in agent.capabilities)
        if score > best_score:
            best_score = score
            best_agent = agent.agent_type
    
    return best_agent


class MultiAgentCoordinator:
    """Coordinates between RLM-VLA agent and other agents (OpenClaw, Gastown, etc.)."""
    
    def __init__(self):
        self.available_agents: list[AgentCapability] = []
        self.task_queue: list[AgentTask] = []
        self._discover_agents()
    
    def _discover_agents(self) -> None:
        """Discover available agents via MCP or API."""
        # Try to discover OpenClaw
        try:
            openclaw = discover_agent_capabilities(AgentType.OPENCLAW)
            if openclaw.mcp_server_url:
                self.available_agents.append(openclaw)
        except:
            pass
        
        # Try to discover Gastown
        try:
            gastown = discover_agent_capabilities(AgentType.GASTOWN)
            if gastown.mcp_server_url:
                self.available_agents.append(gastown)
        except:
            pass
    
    def delegate_task(
        self,
        task: str,
        required_capabilities: list[str],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Delegate a task to the best available agent."""
        # Route to best agent
        agent_type = route_task_to_agent(
            task=task,
            required_capabilities=required_capabilities,
            available_agents=self.available_agents,
        )
        
        if not agent_type:
            return {"error": "no_suitable_agent", "task": task}
        
        # Delegate based on agent type
        if agent_type == AgentType.OPENCLAW:
            return delegate_to_openclaw(task, context)
        elif agent_type == AgentType.GASTOWN:
            return delegate_to_gastown(task, context)
        else:
            return {"error": "unknown_agent_type", "agent": agent_type}
    
    def coordinate_multi_agent_task(
        self,
        main_task: str,
        subtasks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Coordinate a complex task across multiple agents.
        
        Example:
        - RLM-VLA agent: Navigate web, extract data
        - OpenClaw: Save to file, send email
        - Gastown: Coordinate workflow
        """
        results = []
        
        for subtask in subtasks:
            task_desc = subtask.get("task", "")
            capabilities = subtask.get("capabilities", [])
            context = subtask.get("context", {})
            
            result = self.delegate_task(
                task=task_desc,
                required_capabilities=capabilities,
                context=context,
            )
            results.append({
                "subtask": task_desc,
                "result": result,
            })
        
        return {
            "main_task": main_task,
            "subtasks": results,
            "status": "completed",
        }
