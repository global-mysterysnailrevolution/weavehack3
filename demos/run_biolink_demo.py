#!/usr/bin/env python3
"""
Quick script to test the Biolink Depot pricing demo via the API.

This script simulates running the demo through the OpenClaw Beach system.
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_task() -> str:
    """Load the pricing task from file."""
    task_file = Path(__file__).parent / "biolink_pricing_task.txt"
    if task_file.exists():
        return task_file.read_text(encoding="utf-8")
    return """Navigate to https://www.shopbiolinkdepot.org/ and find all products with listed prices. 
For each product, take screenshots, search Google for actual prices, compare images, 
verify vendors, and document pricing differences in a JSON file."""


def run_beach_iteration(api_base: str, goal: str, iteration: int = 0) -> dict:
    """Run a single beach iteration."""
    url = f"{api_base}/api/openclaw/beach"
    
    print(f"\n{'='*70}")
    print(f"Running Beach Iteration {iteration}")
    print(f"{'='*70}\n")
    
    response = requests.post(
        url,
        json={"goal": goal, "iteration": iteration},
        stream=True,
        timeout=300,  # 5 minute timeout
    )
    
    if response.status_code != 200:
        return {
            "error": f"API error: {response.status_code}",
            "status_code": response.status_code,
        }
    
    # Collect all events
    events = []
    score = None
    suggestions = []
    
    for line in response.iter_lines():
        if not line:
            continue
        
        line_str = line.decode("utf-8", errors="replace")
        if line_str.startswith("data: "):
            try:
                data = json.loads(line_str[6:])
                event_type = data.get("type", "")
                
                if event_type == "openclaw_log":
                    print(f"[LOG] {data.get('message', '')}")
                elif event_type == "openclaw_event":
                    events.append(data.get("payload", {}))
                elif event_type == "openclaw_score":
                    score = data.get("score")
                    print(f"\n[SCORE] {score:.2f}")
                elif event_type == "openclaw_suggestions":
                    suggestions = data.get("suggestions", [])
                    print(f"\n[SUGGESTIONS]")
                    for sug in suggestions:
                        print(f"  - {sug}")
                elif event_type == "openclaw_complete":
                    exit_code = data.get("exit_code", -1)
                    print(f"\n[COMPLETE] Exit code: {exit_code}")
            except json.JSONDecodeError:
                pass
    
    return {
        "iteration": iteration,
        "score": score,
        "suggestions": suggestions,
        "events_count": len(events),
        "status": "completed" if score else "unknown",
    }


def main():
    """Run the demo with multiple iterations."""
    api_base = os.getenv("NEXT_PUBLIC_API_BASE_URL", "http://localhost:8000")
    api_base = api_base.rstrip("/")
    
    print("="*70)
    print("BIOLINK DEPOT PRICING DEMO")
    print("="*70)
    print(f"\nAPI Base: {api_base}")
    print("\nThis demo will run multiple iterations to show improvement.")
    print("Each iteration incorporates feedback from the previous run.\n")
    
    goal = load_task()
    
    results = []
    
    # Iteration 0: Initial run
    result_0 = run_beach_iteration(api_base, goal, iteration=0)
    results.append(result_0)
    
    if result_0.get("error"):
        print(f"\n[ERROR] {result_0['error']}")
        return
    
    print(f"\n[ITERATION 0] Score: {result_0.get('score', 'N/A')}")
    
    # Ask if user wants to continue
    if len(result_0.get("suggestions", [])) > 0:
        print("\n" + "="*70)
        print("SUGGESTIONS FOR NEXT ITERATION:")
        print("="*70)
        for i, sug in enumerate(result_0["suggestions"], 1):
            print(f"{i}. {sug}")
        
        response = input("\nRun iteration 1 with these suggestions? (y/n): ").strip().lower()
        if response == "y":
            # Iteration 1: With suggestions
            result_1 = run_beach_iteration(api_base, goal, iteration=1)
            results.append(result_1)
            
            if result_1.get("score"):
                print(f"\n[ITERATION 1] Score: {result_1.get('score')}")
                if result_1.get("score", 0) > result_0.get("score", 0):
                    print("✅ Score improved!")
                else:
                    print("⚠️  Score did not improve")
            
            # Optionally run more iterations
            if result_1.get("score", 0) < 0.9 and len(result_1.get("suggestions", [])) > 0:
                response = input("\nRun iteration 2? (y/n): ").strip().lower()
                if response == "y":
                    result_2 = run_beach_iteration(api_base, goal, iteration=2)
                    results.append(result_2)
                    print(f"\n[ITERATION 2] Score: {result_2.get('score', 'N/A')}")
    
    # Summary
    print("\n" + "="*70)
    print("DEMO SUMMARY")
    print("="*70)
    for i, result in enumerate(results):
        score = result.get("score", "N/A")
        suggestions_count = len(result.get("suggestions", []))
        print(f"Iteration {i}: Score={score}, Suggestions={suggestions_count}")
    
    # Save results
    output_file = Path(__file__).parent / "demo_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[OK] Results saved to: {output_file}")
    
    print("\n" + "="*70)
    print("Check the Marimo dashboard to see:")
    print("  - OpenClaw runs with scores")
    print("  - Prompt evolution across iterations")
    print("  - Performance trends")
    print("="*70)


if __name__ == "__main__":
    main()
