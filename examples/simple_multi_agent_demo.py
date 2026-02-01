"""Simple multi-agent demo that works with or without OpenClaw running."""

import os
from dotenv import load_dotenv

# Ensure Weave is initialized
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

from rvla.agent import run_agent
from rvla.demo import main as demo_main
from rvla.memory import workspace_from_env
from rvla.multi_agent_coordinator import MultiAgentCoordinator, AgentType
from rvla.web import WebDriver

load_dotenv()


def main():
    """Run a simple demo showing multi-agent coordination."""
    
    print("="*70)
    print("RLM-VLA + OpenClaw Integration Demo")
    print("="*70)
    print("\nThis demo shows:")
    print("  1. RLM-VLA agent navigating web")
    print("  2. Multi-agent coordinator discovering agents")
    print("  3. Task delegation to OpenClaw (if available)")
    print("="*70 + "\n")
    
    # Initialize coordinator
    coordinator = MultiAgentCoordinator()
    print(f"[INFO] Discovered {len(coordinator.available_agents)} agents")
    
    # Initialize workspace and driver
    workspace = workspace_from_env()
    driver = WebDriver()
    
    # Simple task
    goal = "Navigate to a website and observe the page"
    
    print(f"[START] Task: {goal}\n")
    
    # Run agent with multi-agent enabled
    result = run_agent(
        goal=goal,
        driver=driver,
        workspace=workspace,
        enable_multi_agent=True,
    )
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"Steps: {len(result['trajectory'])}")
    print(f"Events: {len(result['events'])}")
    print(f"Score: {result['score']}")
    
    # Try delegation (will show attempt even if OpenClaw not running)
    if coordinator.available_agents:
        print("\n[INFO] Attempting to delegate follow-up task to OpenClaw...")
        delegation_result = coordinator.delegate_task(
            task="Save the results to a file",
            required_capabilities=["file_operations"],
            context={"results": str(result)[:500]},
        )
        print(f"Delegation result: {delegation_result.get('status', 'unknown')}")
        if 'error' in delegation_result:
            print(f"Note: {delegation_result.get('error', '')[:100]}")
            print("      This is expected if OpenClaw gateway is not running.")
            print("      To enable: openclaw gateway (in separate terminal)")
    
    print("\n" + "="*70)
    print("Integration framework is working!")
    print("When OpenClaw gateway is running, tasks will be delegated.")
    print("="*70)


if __name__ == "__main__":
    main()
