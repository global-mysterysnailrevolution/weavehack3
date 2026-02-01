"""Optional: Auto-fill hackathon submission form using Browserbase.

This showcases the RLM-VLA agent's browser automation capabilities.
"""

import json
import os
from pathlib import Path

from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver


def main():
    """Auto-fill submission form from generated pack."""
    submission_file = Path("submission_pack/submission.json")
    
    if not submission_file.exists():
        print("❌ submission_pack/submission.json not found!")
        print("   Run: python scripts/generate_submission_pack.py first")
        return
    
    pack = json.loads(submission_file.read_text())
    
    # Build goal for agent
    goal = f"""Navigate to the WeaveHacks 3 submission form and fill it out with this information:

Team Name: {pack.get('team_name', '')}
Project Name: {pack.get('project_name', '')}
Summary: {pack.get('summary', '')}
Utility: {pack.get('utility', '')}
How Built: {pack.get('how_built', '')}
GitHub Link: {pack.get('github_link', '')}
Weave Link: {pack.get('weave_link', '')}

Fill all fields carefully. Take a screenshot before submitting.
DO NOT actually submit - stop before the final submit button."""
    
    print("="*70)
    print("AUTO-FILLING SUBMISSION FORM")
    print("="*70)
    print(f"Goal: {goal[:200]}...")
    print("\n[INFO] Starting agent...")
    print("[INFO] Agent will navigate to form and fill it out")
    print("[INFO] It will stop before submitting (safety)")
    print("="*70 + "\n")
    
    workspace = workspace_from_env()
    driver = WebDriver()
    
    try:
        result = run_agent(
            goal=goal,
            driver=driver,
            workspace=workspace,
            enable_multi_agent=False,
        )
        
        print("\n" + "="*70)
        print("AUTO-FILL COMPLETE")
        print("="*70)
        print(f"Steps: {len(result['trajectory'])}")
        print(f"Score: {result.get('score', {})}")
        
        if result.get('last_observation'):
            obs = result['last_observation']
            print(f"\nFinal URL: {obs.url}")
            if obs.screenshot_base64:
                screenshot_path = Path("submission_pack/filled_form.png")
                import base64
                screenshot_path.write_bytes(base64.b64decode(obs.screenshot_base64))
                print(f"Screenshot saved: {screenshot_path}")
        
    finally:
        driver.close()


if __name__ == "__main__":
    main()
