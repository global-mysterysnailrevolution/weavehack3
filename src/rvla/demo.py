from __future__ import annotations

import os

import wandb
import weave
from dotenv import load_dotenv

from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver


def main() -> None:
    # Load environment variables from .env file
    load_dotenv()
    
    # Initialize W&B
    wandb_api_key = os.getenv("WANDB_API_KEY")
    if wandb_api_key:
        wandb.login(key=wandb_api_key, relogin=True)
        print("[OK] Logged into W&B")
    else:
        print("[WARN] WANDB_API_KEY not found, continuing without W&B login")
    
    # Initialize Weave
    project = os.getenv("WANDB_PROJECT", "weavehacks-rvla")
    entity = os.getenv("WANDB_ENTITY")
    
    # Weave project_name format: "entity/project" or just "project"
    if entity:
        project_name = f"{entity}/{project}"
    else:
        project_name = project
    
    weave.init(project_name)
    print(f"[OK] Initialized Weave: {project_name}")

    # Initialize workspace (Redis or in-memory)
    workspace = workspace_from_env()
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        print("[OK] Using Redis workspace")
        workspace.connect()  # Test connection
    else:
        print("[OK] Using in-memory workspace")
    
    # Initialize driver
    driver = WebDriver()
    
    try:
        # Run agent with a specific goal
        # You can change this to any web navigation task
        goal = "Navigate to a pricing page and extract the pricing table information"
        print(f"\n[START] Starting agent with goal: {goal}\n")
        print(f"[INFO] Using GPT-4o with vision for planning")
        print(f"[INFO] Browserbase session will be created if available\n")
        
        result = run_agent(goal, driver, workspace)

        print("\n" + "="*50)
        print("Run complete")
        print("="*50)
        print(f"Score: {result['score']}")
        print(f"Total steps: {len(result['trajectory'])}")
        print(f"Total events: {len(result['events'])}")
        print("\nRecent events:")
        for event in result["events"][-10:]:
            print(f"  - {event}")
        
        if result.get("last_observation"):
            obs = result["last_observation"]
            print(f"\nLast observation URL: {obs.url}")
    finally:
        # Clean up browser session
        driver.close()


if __name__ == "__main__":
    main()
