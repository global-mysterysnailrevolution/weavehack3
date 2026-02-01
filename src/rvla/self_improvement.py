"""Self-improvement through prompt optimization and strategy learning.

Since we're using OpenAI API (can't tweak weights), we improve by:
1. Analyzing Weave traces to find what works
2. Extracting successful strategies
3. Optimizing prompts based on performance
4. Building a meta-learning layer that updates prompts
"""

from __future__ import annotations

import os
from typing import Any
from dataclasses import dataclass
from collections import defaultdict

import weave

# Ensure Weave is initialized
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

from rvla.openai_client import get_openai_client


@dataclass
class Strategy:
    """A learned strategy from successful runs."""
    pattern: str  # Description of the pattern
    success_rate: float
    context: str  # When this strategy works
    prompt_improvement: str  # How to improve prompt based on this
    examples: list[dict[str, Any]]


@weave.op()
def analyze_weave_traces(
    project_name: str,
    entity: str | None = None,
    min_success_rate: float = 0.7,
) -> list[Strategy]:
    """Analyze Weave traces to extract successful strategies.
    
    This is how we "self-improve" without tweaking weights:
    - Find successful runs
    - Extract patterns
    - Learn what prompts/strategies work
    - Update future prompts based on learnings
    """
    # In a real implementation, we'd query Weave API for traces
    # For now, this is a framework for how it would work
    
    strategies = []
    
    # TODO: Query Weave API for traces
    # traces = weave_client.get_traces(project=project_name, entity=entity)
    # successful_traces = [t for t in traces if t.score > min_success_rate]
    
    # For demo, return example strategies
    strategies.append(Strategy(
        pattern="Navigate then observe pattern",
        success_rate=0.85,
        context="When navigating to new pages",
        prompt_improvement="After navigation, always observe before planning next action",
        examples=[{"action": "navigate", "next": "observe", "success": True}],
    ))
    
    return strategies


@weave.op()
def optimize_prompt(
    base_prompt: str,
    strategies: list[Strategy],
    current_context: str,
) -> str:
    """Optimize a prompt based on learned strategies.
    
    This is the "weight tweaking" equivalent for API-based models:
    we improve the prompt based on what we've learned works.
    """
    client = get_openai_client()
    
    # Find relevant strategies
    relevant_strategies = [
        s for s in strategies
        if s.context.lower() in current_context.lower() or s.success_rate > 0.8
    ]
    
    if not relevant_strategies:
        return base_prompt
    
    # Build improvement suggestions
    improvements = "\n".join([
        f"- {s.prompt_improvement} (success rate: {s.success_rate:.0%})"
        for s in relevant_strategies[:3]  # Top 3
    ])
    
    prompt = f"""Optimize this prompt based on successful strategies learned from past runs.

Base Prompt:
{base_prompt}

Learned Strategies:
{improvements}

Create an improved version of the prompt that incorporates these learnings.
Return only the improved prompt, no explanation."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a prompt optimization expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1000,
    )
    
    return response.choices[0].message.content


@weave.op()
def extract_strategy_from_trace(
    trace_data: dict[str, Any],
) -> Strategy | None:
    """Extract a strategy pattern from a single Weave trace."""
    # Analyze trace to find patterns
    actions = trace_data.get("actions", [])
    success = trace_data.get("success", False)
    
    if not success or len(actions) < 2:
        return None
    
    # Find common patterns
    patterns = []
    for i in range(len(actions) - 1):
        pattern = f"{actions[i]['type']} → {actions[i+1]['type']}"
        patterns.append(pattern)
    
    # Count pattern frequency
    pattern_counts = defaultdict(int)
    for pattern in patterns:
        pattern_counts[pattern] += 1
    
    # Most common pattern
    if pattern_counts:
        most_common = max(pattern_counts.items(), key=lambda x: x[1])
        return Strategy(
            pattern=most_common[0],
            success_rate=1.0 if success else 0.0,
            context=trace_data.get("goal", ""),
            prompt_improvement=f"Use pattern: {most_common[0]}",
            examples=[trace_data],
        )
    
    return None


class SelfImprovingAgent:
    """Agent that improves through prompt optimization, not weight tweaking."""
    
    def __init__(self, project_name: str, entity: str | None = None):
        self.project_name = project_name
        self.entity = entity
        self.strategies: list[Strategy] = []
        self.prompt_cache: dict[str, str] = {}
    
    def learn_from_traces(self) -> None:
        """Learn strategies from Weave traces."""
        self.strategies = analyze_weave_traces(
            project_name=self.project_name,
            entity=self.entity,
        )
    
    def get_optimized_prompt(
        self,
        base_prompt: str,
        context: str,
    ) -> str:
        """Get an optimized prompt based on learned strategies."""
        cache_key = f"{base_prompt[:50]}:{context[:50]}"
        if cache_key in self.prompt_cache:
            return self.prompt_cache[cache_key]
        
        optimized = optimize_prompt(base_prompt, self.strategies, context)
        self.prompt_cache[cache_key] = optimized
        return optimized
    
    def update_from_run(
        self,
        trace_data: dict[str, Any],
    ) -> None:
        """Update strategies based on a completed run."""
        strategy = extract_strategy_from_trace(trace_data)
        if strategy:
            # Add or update strategy
            existing = next(
                (s for s in self.strategies if s.pattern == strategy.pattern),
                None
            )
            if existing:
                # Update success rate (moving average)
                existing.success_rate = (existing.success_rate + strategy.success_rate) / 2
                existing.examples.append(strategy.examples[0])
            else:
                self.strategies.append(strategy)
