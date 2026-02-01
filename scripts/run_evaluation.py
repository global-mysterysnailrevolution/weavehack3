#!/usr/bin/env python3
"""Run Weave evaluation on the RLM-VLA agent."""

import os
import sys
import asyncio
from pathlib import Path

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

from rvla.evaluation import (
    RLMVLAModel,
    create_pricing_evaluation_dataset,
    create_general_evaluation_dataset,
    run_evaluation,
    AgentTask,
)

print("="*70)
print("WEAVE EVALUATION - RLM-VLA AGENT")
print("="*70)
print()

# Initialize Weave
entity = os.getenv("WANDB_ENTITY", "")
project = os.getenv("WANDB_PROJECT", "weavehacks-rvla")

if entity:
    weave.init(f"{entity}/{project}")
else:
    weave.init(project)

print(f"Initialized Weave: {entity}/{project if entity else project}")
print()

# Create model
print("Creating RLM-VLA Model...")
model = RLMVLAModel(
    model_name="gpt-4o",
    enable_multi_agent=False,
)
print("✅ Model created")
print()

# Choose dataset
print("Select dataset:")
print("1. Pricing extraction (shopbiolinkdepot tasks)")
print("2. General navigation")
choice = input("Enter choice (1 or 2, default=1): ").strip() or "1"

if choice == "2":
    print("\nCreating general navigation dataset...")
    dataset = create_general_evaluation_dataset()
    eval_name = "general_navigation_eval"
else:
    print("\nCreating pricing extraction dataset...")
    dataset = create_pricing_evaluation_dataset()
    eval_name = "pricing_extraction_eval"

print(f"✅ Dataset created: {dataset.name}")
print(f"   Examples: {len(dataset.rows)}")
print()

# Run evaluation
print("Running evaluation...")
print("This may take a few minutes as the agent completes each task...")
print()

try:
    results = run_evaluation(model, dataset, name=eval_name)
    
    print("="*70)
    print("EVALUATION RESULTS")
    print("="*70)
    print()
    print(f"Evaluation: {eval_name}")
    print(f"Dataset: {dataset.name}")
    print(f"Model: {model.model_name}")
    print()
    
    # Print summary
    if isinstance(results, dict):
        print("Summary:")
        for key, value in results.items():
            if isinstance(value, (int, float, str, bool)):
                print(f"  {key}: {value}")
        print()
    
    print("✅ Evaluation complete!")
    print()
    print(f"View results in Weave: https://wandb.ai/{entity}/{project}/weave" if entity else f"View results in Weave: https://wandb.ai/{project}/weave")
    
except Exception as e:
    print(f"❌ Error running evaluation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
