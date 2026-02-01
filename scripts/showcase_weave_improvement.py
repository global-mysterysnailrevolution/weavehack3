#!/usr/bin/env python3
"""
Showcase Weave-driven iterative improvement for Biolink pricing task.

This script demonstrates:
1. Initial run with Weave tracing
2. Analysis of Weave traces to identify issues
3. Iterative improvement based on findings
4. Visualization of improvement over time
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rvla.weave_init import ensure_weave_init
from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver
from rvla.self_improvement import analyze_weave_traces, optimize_prompt

ensure_weave_init()
import weave

load_dotenv()


@weave.op()
def run_pricing_iteration(
    iteration: int,
    goal: str,
    previous_feedback: str = "",
) -> dict:
    """Run a single iteration of the pricing task, logged to Weave."""
    
    workspace = workspace_from_env()
    driver = WebDriver()
    
    # Enhance goal with feedback from previous iteration
    enhanced_goal = goal
    if previous_feedback:
        enhanced_goal = f"{goal}\n\nImprovements from previous run:\n{previous_feedback}"
    
    try:
        result = run_agent(
            goal=enhanced_goal,
            driver=driver,
            workspace=workspace,
            enable_multi_agent=False,
        )
        
        return {
            "iteration": iteration,
            "success": result.get("score", {}).get("success_rate", 0) > 0.5,
            "steps": len(result.get("trajectory", [])),
            "events": len(result.get("events", [])),
            "score": result.get("score", {}),
            "trajectory_summary": [
                {"type": a.type, "command": a.payload.get("command", "")}
                for a in result.get("trajectory", [])[:10]  # First 10 actions
            ],
        }
    finally:
        driver.close()


def analyze_iteration_results(results: dict) -> dict:
    """Analyze iteration results and generate improvement suggestions."""
    analysis = {
        "iteration": results["iteration"],
        "success": results["success"],
        "issues": [],
        "suggestions": [],
        "metrics": {
            "steps": results["steps"],
            "events": results["events"],
            "score": results.get("score", {}),
        },
    }
    
    # Check for common issues
    trajectory = results.get("trajectory_summary", [])
    
    # Check if agent navigated to the store
    has_navigation = any(
        "navigate" in str(action.get("command", "")).lower() 
        or "shopbiolinkdepot" in str(action).lower()
        for action in trajectory
    )
    
    if not has_navigation:
        analysis["issues"].append("Agent did not navigate to shopbiolinkdepot.org")
        analysis["suggestions"].append("Add explicit navigation step: 'Navigate to https://www.shopbiolinkdepot.org/'")
    
    # Check for Google searches
    has_search = any(
        "google" in str(action).lower() or "search" in str(action).lower()
        for action in trajectory
    )
    
    if not has_search:
        analysis["issues"].append("Agent did not perform Google searches")
        analysis["suggestions"].append("Add explicit Google search steps for each product")
    
    # Check for screenshots
    has_screenshots = any(
        "screenshot" in str(action).lower() or "observe" in str(action.get("command", "")).lower()
        for action in trajectory
    )
    
    if not has_screenshots:
        analysis["issues"].append("Agent did not take screenshots")
        analysis["suggestions"].append("Take screenshots of product pages showing prices")
    
    # Check for price extraction
    events = results.get("events", [])
    has_pricing = any(
        "price" in str(event).lower() or "pricing" in str(event).lower()
        for event in events
    )
    
    if not has_pricing:
        analysis["issues"].append("Agent did not extract pricing information")
        analysis["suggestions"].append("Explicitly extract and document prices from both sources")
    
    # Check step count (too few might mean incomplete)
    if results["steps"] < 5:
        analysis["issues"].append("Very few steps taken - task may be incomplete")
        analysis["suggestions"].append("Break down the task into smaller, explicit steps")
    
    return analysis


def generate_improvement_feedback(analyses: list[dict]) -> str:
    """Generate feedback string from multiple iteration analyses."""
    if not analyses:
        return ""
    
    latest = analyses[-1]
    feedback_lines = []
    
    if latest["issues"]:
        feedback_lines.append("Issues identified:")
        for issue in latest["issues"]:
            feedback_lines.append(f"  - {issue}")
    
    if latest["suggestions"]:
        feedback_lines.append("\nSuggested improvements:")
        for suggestion in latest["suggestions"]:
            feedback_lines.append(f"  - {suggestion}")
    
    # Compare with previous iteration if available
    if len(analyses) > 1:
        prev = analyses[-2]
        if latest["steps"] > prev["steps"]:
            feedback_lines.append(f"\n✅ Improved: Took more steps ({latest['steps']} vs {prev['steps']})")
        if latest["success"] and not prev["success"]:
            feedback_lines.append("\n✅ Improved: Task now succeeds!")
    
    return "\n".join(feedback_lines)


def main():
    """Run iterative improvement showcase."""
    
    print("="*70)
    print("WEAVE-DRIVEN ITERATIVE IMPROVEMENT SHOWCASE")
    print("="*70)
    print()
    print("This demo shows how Weave traces enable iterative improvement:")
    print("  1. Run initial task")
    print("  2. Analyze Weave traces to identify issues")
    print("  3. Generate improvement suggestions")
    print("  4. Run again with improvements")
    print("  5. Compare results and iterate")
    print()
    
    base_goal = """Navigate to https://www.shopbiolinkdepot.org/ and find products with prices. For each product: take a screenshot, search Google for the product name, compare images, verify vendors, and document price differences. Save findings to JSON."""
    
    num_iterations = int(os.getenv("WEAVE_ITERATIONS", "3"))
    
    print(f"Running {num_iterations} iterations...")
    print()
    
    all_results = []
    all_analyses = []
    previous_feedback = ""
    
    for iteration in range(num_iterations):
        print(f"{'='*70}")
        print(f"ITERATION {iteration + 1}/{num_iterations}")
        print(f"{'='*70}")
        print()
        
        if previous_feedback:
            print("Previous feedback:")
            print("-" * 70)
            print(previous_feedback)
            print("-" * 70)
            print()
        
        print(f"Running iteration {iteration + 1}...")
        start_time = time.time()
        
        # Run iteration (logged to Weave)
        result = run_pricing_iteration(
            iteration=iteration + 1,
            goal=base_goal,
            previous_feedback=previous_feedback,
        )
        
        elapsed = time.time() - start_time
        
        print(f"✅ Completed in {elapsed:.1f}s")
        print(f"   Steps: {result['steps']}")
        print(f"   Events: {result['events']}")
        print(f"   Success: {result['success']}")
        print()
        
        all_results.append(result)
        
        # Analyze results
        print("Analyzing results...")
        analysis = analyze_iteration_results(result)
        all_analyses.append(analysis)
        
        if analysis["issues"]:
            print(f"⚠️  Found {len(analysis['issues'])} issues:")
            for issue in analysis["issues"]:
                print(f"   - {issue}")
        else:
            print("✅ No major issues found!")
        
        if analysis["suggestions"]:
            print(f"💡 Generated {len(analysis['suggestions'])} suggestions")
        
        print()
        
        # Generate feedback for next iteration
        previous_feedback = generate_improvement_feedback(all_analyses)
        
        # Wait a bit between iterations
        if iteration < num_iterations - 1:
            print("Waiting 2 seconds before next iteration...")
            time.sleep(2)
            print()
    
    # Final summary
    print()
    print("="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print()
    
    print("Iteration Comparison:")
    print("-" * 70)
    print(f"{'Iteration':<12} {'Steps':<8} {'Events':<8} {'Success':<10} {'Issues':<8}")
    print("-" * 70)
    for i, (result, analysis) in enumerate(zip(all_results, all_analyses)):
        print(f"{i+1:<12} {result['steps']:<8} {result['events']:<8} {str(result['success']):<10} {len(analysis['issues']):<8}")
    print("-" * 70)
    print()
    
    # Check for improvement
    if len(all_results) > 1:
        first = all_results[0]
        last = all_results[-1]
        
        print("Improvement Metrics:")
        print(f"  Steps: {first['steps']} → {last['steps']} ({last['steps'] - first['steps']:+d})")
        print(f"  Events: {first['events']} → {last['events']} ({last['events'] - first['events']:+d})")
        print(f"  Success: {first['success']} → {last['success']}")
        print()
        
        if last['steps'] > first['steps'] and last['success']:
            print("✅ Improvement detected! Agent is getting better.")
        elif len(all_analyses[-1]['issues']) < len(all_analyses[0]['issues']):
            print("✅ Improvement detected! Fewer issues in later iterations.")
        else:
            print("⚠️  Limited improvement - may need more iterations or different approach.")
        print()
    
    # Save results
    output_file = Path(__file__).parent.parent / "weave_improvement_showcase.json"
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "iterations": [
            {
                "iteration": r["iteration"],
                "result": r,
                "analysis": a,
            }
            for r, a in zip(all_results, all_analyses)
        ],
        "summary": {
            "total_iterations": num_iterations,
            "final_success": all_results[-1]["success"] if all_results else False,
            "improvement_detected": (
                len(all_results) > 1 and
                (all_results[-1]["steps"] > all_results[0]["steps"] or
                 len(all_analyses[-1]["issues"]) < len(all_analyses[0]["issues"]))
            ),
        },
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✅ Results saved to: {output_file}")
    print()
    print("Next Steps:")
    print("  1. Check Weave dashboard to see detailed traces for each iteration")
    print("  2. Review Marimo dashboard for visualization of improvements")
    print("  3. Compare Weave traces between iterations to see what changed")
    print("  4. Use the suggestions to further refine the agent")
    print()
    print("Weave Project:", os.getenv("WANDB_PROJECT", "weavehacks-rvla"))
    print("Weave Entity:", os.getenv("WANDB_ENTITY", "default"))
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
