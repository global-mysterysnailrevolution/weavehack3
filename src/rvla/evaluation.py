"""Weave Evaluation pipeline for RLM-VLA agent.

This implements formal evaluations using Weave's Model and Evaluation classes
to systematically test and improve the agent.
"""

from __future__ import annotations

import os
from typing import Any
from dataclasses import dataclass

import weave
from weave.scorers import MultiTaskBinaryClassificationF1

# Ensure Weave is initialized
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver


@dataclass
class AgentTask:
    """A task for the agent to complete."""
    id: str
    goal: str
    target: dict[str, Any]  # Expected outcome
    context: str | None = None  # Additional context


class RLMVLAModel(weave.Model):
    """Weave Model wrapper for RLM-VLA agent."""
    
    model_name: str = "gpt-4o"
    enable_multi_agent: bool = False
    
    @weave.op()
    async def predict(self, task: AgentTask) -> dict[str, Any]:
        """Run the agent on a task and return results."""
        workspace = workspace_from_env()
        driver = WebDriver()
        
        try:
            result = run_agent(
                goal=task.goal,
                driver=driver,
                workspace=workspace,
                enable_multi_agent=self.enable_multi_agent,
            )
            
            return {
                "success": result.get("score", {}).get("success", False),
                "steps": len(result.get("trajectory", [])),
                "events": result.get("events", []),
                "score": result.get("score", {}),
                "last_observation": {
                    "url": result.get("last_observation", {}).url if result.get("last_observation") else None,
                } if result.get("last_observation") else None,
            }
        finally:
            driver.close()


@weave.op()
def task_success_score(target: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    """Score whether the agent successfully completed the task."""
    # Check if agent reported success
    agent_success = output.get("success", False)
    
    # Check if target criteria are met
    target_checks = target.get("checks", {})
    checks_passed = 0
    total_checks = len(target_checks) if target_checks else 1
    
    if target_checks:
        # Check each target criterion
        if "min_steps" in target_checks:
            if output.get("steps", 0) >= target_checks["min_steps"]:
                checks_passed += 1
        if "max_steps" in target_checks:
            if output.get("steps", 0) <= target_checks["max_steps"]:
                checks_passed += 1
        if "required_events" in target_checks:
            events = output.get("events", [])
            required = target_checks["required_events"]
            if all(req in str(events).lower() for req in required):
                checks_passed += 1
    else:
        # If no specific checks, just use agent's success
        checks_passed = 1 if agent_success else 0
    
    return {
        "success": agent_success and (checks_passed / total_checks) >= 0.5,
        "checks_passed": checks_passed,
        "total_checks": total_checks,
    }


@weave.op()
def efficiency_score(target: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    """Score agent efficiency (fewer steps is better, but must succeed)."""
    success = output.get("success", False)
    steps = output.get("steps", 0)
    
    # Ideal steps (if specified in target)
    ideal_steps = target.get("ideal_steps", 10)
    
    if not success:
        return {"efficient": False, "steps_ratio": 0.0}
    
    # Efficiency: closer to ideal is better
    if steps == 0:
        return {"efficient": False, "steps_ratio": 0.0}
    
    ratio = ideal_steps / max(steps, 1)
    return {
        "efficient": ratio >= 0.7,  # Within 30% of ideal
        "steps_ratio": min(1.0, ratio),
    }


def create_pricing_evaluation_dataset() -> weave.Dataset:
    """Create a dataset for evaluating pricing extraction tasks."""
    examples = [
        {
            "id": "pricing_1",
            "goal": "Navigate to shopbiolinkdepot.org, find pricing for 'Biolink Premium Cable', extract the price, search Google for the same product, and compare prices. Save results to JSON.",
            "target": {
                "checks": {
                    "min_steps": 5,
                    "required_events": ["navigate", "extract", "search", "compare", "save"],
                },
                "ideal_steps": 8,
            },
        },
        {
            "id": "pricing_2",
            "goal": "Go to shopbiolinkdepot.org, find 3 products with prices, search for each on Google, verify they're legitimate vendors (not just eBay), and create a comparison report.",
            "target": {
                "checks": {
                    "min_steps": 10,
                    "required_events": ["navigate", "extract", "search", "verify", "report"],
                },
                "ideal_steps": 15,
            },
        },
    ]
    
    dataset = weave.Dataset(name="pricing_extraction", rows=examples)
    weave.publish(dataset)
    return dataset


def create_general_evaluation_dataset() -> weave.Dataset:
    """Create a dataset for general web navigation tasks."""
    examples = [
        {
            "id": "nav_1",
            "goal": "Navigate to example.com and extract the main heading.",
            "target": {
                "checks": {
                    "min_steps": 2,
                    "required_events": ["navigate", "extract"],
                },
                "ideal_steps": 3,
            },
        },
        {
            "id": "nav_2",
            "goal": "Go to a website, take a screenshot, and describe what you see.",
            "target": {
                "checks": {
                    "min_steps": 3,
                    "required_events": ["navigate", "screenshot", "describe"],
                },
                "ideal_steps": 4,
            },
        },
    ]
    
    dataset = weave.Dataset(name="general_navigation", rows=examples)
    weave.publish(dataset)
    return dataset


def run_evaluation(
    model: RLMVLAModel,
    dataset: weave.Dataset,
    name: str = "agent_eval",
) -> dict[str, Any]:
    """Run an evaluation on a model with a dataset."""
    evaluation = weave.Evaluation(
        name=name,
        dataset=dataset,
        scorers=[
            task_success_score,
            efficiency_score,
            MultiTaskBinaryClassificationF1(class_names=["success", "efficient"]),
        ],
    )
    
    import asyncio
    return asyncio.run(evaluation.evaluate(model))


if __name__ == "__main__":
    # Example usage
    weave.init(os.getenv("WANDB_PROJECT", "weavehacks-rvla"))
    
    # Create model
    model = RLMVLAModel(
        model_name="gpt-4o",
        enable_multi_agent=False,
    )
    
    # Create dataset
    dataset = create_pricing_evaluation_dataset()
    
    # Run evaluation
    results = run_evaluation(model, dataset, name="pricing_extraction_eval")
    print("Evaluation Results:")
    print(results)
