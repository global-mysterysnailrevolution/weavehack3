"""Demo: RLM-VLA agent coordinating with OpenClaw for a complete workflow."""

import os
from dotenv import load_dotenv

# Ensure Weave is initialized
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.multi_agent_coordinator import MultiAgentCoordinator
from rvla.web import WebDriver

load_dotenv()


def demo_web_research_with_file_save():
    """Demo: RLM-VLA navigates web, OpenClaw saves results."""
    
    print("="*70)
    print("DEMO: Multi-Agent Web Research")
    print("="*70)
    print("\nTask: Navigate to a pricing page, extract data, save to file")
    print("\nAgents:")
    print("  - RLM-VLA: Web navigation and data extraction")
    print("  - OpenClaw: File operations and organization")
    print("="*70 + "\n")
    
    # Initialize
    workspace = workspace_from_env()
    driver = WebDriver()
    coordinator = MultiAgentCoordinator()
    
    # Step 1: RLM-VLA agent navigates and extracts
    print("[RLM-VLA] Starting web navigation...")
    result = run_agent(
        goal="Navigate to a SaaS pricing page and extract all pricing tiers with features",
        driver=driver,
        workspace=workspace,
        enable_multi_agent=True,
    )
    
    print(f"\n[RLM-VLA] Completed: {len(result['trajectory'])} steps")
    print(f"[RLM-VLA] Events: {len(result['events'])}")
    
    # Step 2: Delegate file operations to OpenClaw
    print("\n[OPENCLAW] Delegating file operations...")
    
    # Extract any data from result
    extracted_data = {
        "url": result.get("last_observation", {}).get("url", "unknown"),
        "events": result["events"][-10:],  # Last 10 events
        "score": result["score"],
    }
    
    file_result = coordinator.delegate_task(
        task="Save extracted pricing data to a JSON file in organized folder structure",
        required_capabilities=["file_operations"],
        context={
            "data": extracted_data,
            "filename": "pricing_research.json",
            "folder": "research_data",
        },
    )
    
    print(f"[OPENCLAW] Result: {file_result}")
    
    # Summary
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print(f"RLM-VLA steps: {len(result['trajectory'])}")
    print(f"OpenClaw delegation: {file_result.get('status', 'unknown')}")
    print("\nThis demonstrates:")
    print("  ✓ RLM-VLA handles complex web navigation")
    print("  ✓ Multi-agent coordination")
    print("  ✓ Task delegation based on capabilities")
    print("="*70)


def demo_with_gateway_check():
    """Demo with gateway status check."""
    import subprocess
    
    print("Checking OpenClaw gateway status...")
    try:
        result = subprocess.run(
            ["openclaw", "status"],
            capture_output=True,
            text=True,
            timeout=5,
            shell=True,
        )
        if "unreachable" in result.stdout or "not running" in result.stdout.lower():
            print("\n[INFO] OpenClaw gateway is not running")
            print("To start: openclaw gateway (in separate terminal)")
            print("Or: openclaw gateway --port 18789")
            print("\nContinuing with mock integration...")
    except:
        pass
    
    # Run demo anyway (will show delegation attempt)
    demo_web_research_with_file_save()


if __name__ == "__main__":
    demo_with_gateway_check()
