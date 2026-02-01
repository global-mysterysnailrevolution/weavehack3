#!/usr/bin/env python3
"""
Quick demo that works immediately - uses mock data if needed.

This creates a simple demo showing iterative improvement without
requiring full agent runs (which can be slow).
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from rvla.weave_init import ensure_weave_init
ensure_weave_init()
import weave


@weave.op()
def mock_iteration(iteration: int, feedback: str = "") -> dict:
    """Mock iteration for quick demo - logs to Weave."""
    
    # Simulate improvement over iterations
    base_steps = 8 + (iteration * 7)
    base_events = 12 + (iteration * 16)
    base_score = 0.5 + (iteration * 0.15)
    
    return {
        "iteration": iteration,
        "steps": base_steps,
        "events": base_events,
        "success": iteration > 1,
        "score": {
            "success_rate": base_score,
            "completeness": min(1.0, 0.4 + (iteration * 0.2)),
        },
        "trajectory_summary": [
            {"type": "navigate", "command": "navigate"},
            {"type": "observe", "command": "observe"},
            {"type": "extract", "command": "extract"},
        ] * iteration,
    }


def main():
    """Run quick demo with mock iterations."""
    
    print("="*70)
    print("🦞 LOBSTER POT - QUICK DEMO")
    print("="*70)
    print()
    print("This is a quick demo showing iterative improvement.")
    print("Each iteration is logged to Weave and shows improvement.")
    print()
    
    results = []
    feedback = ""
    
    for i in range(3):
        print(f"{'='*70}")
        print(f"ITERATION {i+1}/3")
        print(f"{'='*70}")
        print()
        
        if feedback:
            print("📋 Feedback from previous run:")
            print("-" * 70)
            print(feedback[:150] + "...")
            print("-" * 70)
            print()
        
        print(f"🚀 Running iteration {i+1}...")
        
        # Run mock iteration (logged to Weave)
        result = mock_iteration(iteration=i+1, feedback=feedback)
        
        print(f"✅ Completed!")
        print(f"   Steps: {result['steps']}")
        print(f"   Events: {result['events']}")
        print(f"   Success: {result['success']}")
        print(f"   Score: {result['score']['success_rate']:.2f}")
        print()
        
        results.append(result)
        
        # Generate feedback
        if i == 0:
            feedback = "Issues identified:\n  - Agent did not navigate to shopbiolinkdepot.org\n  - Agent did not perform Google searches\n\nSuggested improvements:\n  - Add explicit navigation step\n  - Add Google search steps for each product"
        elif i == 1:
            feedback = "Issues identified:\n  - Incomplete documentation\n\nSuggested improvements:\n  - Ensure output is saved in structured JSON format"
        else:
            feedback = "✅ All issues resolved!"
        
        if i < 2:
            import time
            time.sleep(1)
            print()
    
    # Summary
    print("="*70)
    print("🎉 DEMO COMPLETE!")
    print("="*70)
    print()
    print("Improvement Summary:")
    for i, r in enumerate(results, 1):
        print(f"  Iteration {i}: {r['steps']} steps, Score {r['score']['success_rate']:.2f}")
    print()
    print(f"✅ Improvement: {results[0]['score']['success_rate']:.2f} → {results[-1]['score']['success_rate']:.2f}")
    print()
    print("Next steps:")
    print("  1. Check Weave dashboard for traces")
    print("  2. View Marimo dashboard for visualization")
    print("  3. Run full demo: python scripts/hackathon_demo.py")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
