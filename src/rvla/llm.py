from __future__ import annotations

import base64
import os
from typing import Any

import weave

# Ensure Weave is initialized
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

from rvla.openai_client import get_openai_client


@weave.op()
def plan_next_action(
    goal: str,
    observation: dict[str, Any] | None,
    history: list[str],
    depth: int,
    screenshot_base64: str | None = None,
) -> dict[str, Any]:
    """Use GPT-4o to plan the next action based on goal, observation, history, and screenshot."""
    client = get_openai_client()

    # Use adaptive context window based on depth and history length
    # For deeper recursion or longer history, use more context
    context_window = 10
    if depth > 0:
        context_window = 15  # More context for recursive calls
    if len(history) > 50:
        context_window = 20  # More context for long-running tasks
    
    history_context = "\n".join(history[-context_window:]) if history else "No history yet."
    obs_context = ""
    if observation:
        obs_context = f"Current URL: {observation.get('url', 'unknown')}\n"
        if observation.get("metadata"):
            obs_context += f"Metadata: {observation['metadata']}\n"

    # Build messages with vision support
    messages = [
        {
            "role": "system",
            "content": "You are an expert web navigation agent. Analyze screenshots carefully and plan precise actions. Always respond with valid JSON."
        }
    ]
    
    # Build user message with text and optionally image
    user_content = f"""You are a web navigation agent. Your goal is: {goal}

Recent history:
{history_context}

{obs_context}

Current depth: {depth}

For complex tasks involving multiple products or items:
- Use "subcall" to break down the task into smaller subtasks (e.g., "Verify pricing for product X")
- Each subcall can handle one product or one verification step
- Navigate between websites as needed (e.g., Biolink Depot -> Google search -> vendor sites)

Analyze the current page state and decide what to do next. Respond with JSON:
{{
  "action_type": "act" | "subcall" | "done",
  "reasoning": "brief explanation of what you see and why you chose this action",
  "task": "if action_type is subcall, the subtask to delegate (e.g., 'Search Google for product X and verify pricing')",
  "command": "if action_type is act, the browser command (observe, click, type, scroll, navigate)",
  "target": "if command needs a target (e.g., CSS selector, XPath, visible text, or URL for navigate)",
  "text": "if command is 'type', the text to type"
}}

Available action types:
- "act": Perform a browser action (observe, click, type, scroll, navigate)
- "subcall": Delegate a subtask to a recursive sub-agent when the task needs decomposition
- "done": Task is complete or cannot proceed further

Available commands for "act":
- "observe": Take a screenshot and get page state (use when you need to see the page)
- "click": Click an element (requires target - describe what to click: button text, link text, or element description)
- "type": Type text into an input field (requires target and text)
- "scroll": Scroll the page (up or down)
- "navigate": Navigate to a URL (requires target URL)

When analyzing screenshots:
- Look for pricing tables, buttons, forms, links, and other interactive elements
- Describe elements clearly in the target field (e.g., "Pricing" button, "Sign up" link, "Email" input field)
- If you see a pricing table, extract it or navigate to find it
- Be specific about what you're clicking or interacting with

Respond only with valid JSON."""

    # Add screenshot if available
    if screenshot_base64:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_content},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{screenshot_base64}",
                        "detail": "high"
                    }
                }
            ]
        })
    else:
        messages.append({"role": "user", "content": user_content})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=1000,
    )

    import json
    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI API returned empty content")
    result = json.loads(content)
    return result


@weave.op()
def analyze_observation(
    goal: str,
    screenshot_base64: str | None,
    url: str | None = None,
) -> dict[str, Any]:
    """Use GPT-4o vision to analyze a screenshot and extract relevant information."""
    client = get_openai_client()

    if not screenshot_base64:
        return {"analysis": "No screenshot available", "relevant_elements": [], "suggested_actions": []}

    prompt = f"""Analyze this screenshot in the context of the goal: {goal}

Current URL: {url or 'unknown'}

Extract:
1. What is visible on the page? Describe the layout, content, and key elements.
2. Are there any elements relevant to the goal (e.g., pricing tables, buttons, forms)?
3. What specific actions would help achieve the goal?

Respond with JSON:
{{
  "description": "detailed description of what you see on the page",
  "relevant_elements": ["list of element descriptions that relate to the goal"],
  "suggested_actions": ["list of specific suggested next actions with details"],
  "has_pricing_table": true/false,
  "page_type": "landing page" | "pricing page" | "product page" | "other"
}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert at analyzing web pages. Provide detailed, actionable insights. Always respond with valid JSON."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{screenshot_base64}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1000,
    )

    import json
    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI API returned empty content")
    result = json.loads(content)
    return result
