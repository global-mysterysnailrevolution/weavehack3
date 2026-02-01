"""Example: RLM-VLA agent coordinating with OpenClaw and Gastown."""

# Ensure Weave is initialized
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

from rvla.agent import run_agent
from rvla.demo import main as demo_main
from rvla.memory import workspace_from_env
from rvla.multi_agent_coordinator import MultiAgentCoordinator
from rvla.web import WebDriver


def multi_agent_example():
    """Example showing RLM-VLA agent working with OpenClaw."""
    
    # Setup
    workspace = workspace_from_env()
    driver = WebDriver()
    coordinator = MultiAgentCoordinator()
    
    # Register OpenClaw (if running)
    coordinator.register_server("openclaw", "http://localhost:3000/mcp")
    
    # Task that requires both agents
    goal = "Navigate to pricing page, extract data, save to file, send summary"
    
    print(f"[START] Multi-agent task: {goal}\n")
    
    # Run RLM-VLA agent for web navigation
    result = run_agent(
        goal="Navigate to pricing page and extract pricing data",
        driver=driver,
        workspace=workspace,
        enable_multi_agent=True,
    )
    
    # Extract data from result
    extracted_data = result.get("extracted_data", {})
    
    # Delegate file operations to OpenClaw
    if coordinator.available_agents:
        file_task = coordinator.delegate_task(
            task=f"Save pricing data to file: {extracted_data}",
            required_capabilities=["file_operations"],
            context={"data": extracted_data, "filename": "pricing_data.json"},
        )
        print(f"[OPENCLAW] File operation: {file_task}")
        
        # Delegate email to OpenClaw
        email_task = coordinator.delegate_task(
            task="Send email summary of pricing data",
            required_capabilities=["email_sending"],
            context={"summary": str(extracted_data)[:500]},
        )
        print(f"[OPENCLAW] Email task: {email_task}")
    
    print("\n[COMPLETE] Multi-agent task finished")


def gastown_coordination_example():
    """Example showing Gastown coordinating multiple agents."""
    
    coordinator = MultiAgentCoordinator()
    
    # Register agents
    coordinator.register_server("openclaw", "http://localhost:3000/mcp")
    coordinator.register_server("gastown", "http://localhost:8080/mcp")
    
    # Complex multi-agent task
    result = coordinator.coordinate_multi_agent_task(
        main_task="Complete research project",
        subtasks=[
            {
                "task": "Navigate web and extract research data",
                "capabilities": ["web_navigation", "data_extraction"],
                "context": {"urls": ["site1.com", "site2.com"]},
            },
            {
                "task": "Save data to organized file structure",
                "capabilities": ["file_operations"],
                "context": {"data": "extracted_data"},
            },
            {
                "task": "Send summary email",
                "capabilities": ["email_sending"],
                "context": {"summary": "research findings"},
            },
        ],
    )
    
    print(f"[GASTOWN] Coordination result: {result}")


if __name__ == "__main__":
    # Run multi-agent demo
    multi_agent_example()
