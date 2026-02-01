from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import weave

# Ensure Weave is initialized before any ops
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

from rvla.llm import analyze_observation, plan_next_action
from rvla.memory import Workspace
from rvla.multi_agent_coordinator import MultiAgentCoordinator, AgentType
from rvla.rlm_core import RLMContextExaminer
from rvla.visual_rlm import VisualRLMExaminer
from rvla.web import Action, Observation, WebDriver


@dataclass
class AgentState:
    goal: str
    depth: int = 0
    max_depth: int = 5  # Increased for better recursion in complex tasks
    step_count: int = 0
    parent_goal: str | None = None  # Track parent goal for context


@weave.op()
def inspect_history(query: str, events: list[str]) -> list[str]:
    """Search through event history for matching events."""
    return [event for event in events if query.lower() in event.lower()]


@weave.op()
def crop_image(image_path: str | None, bbox: tuple[int, int, int, int]) -> dict[str, Any]:
    return {
        "image_path": image_path,
        "bbox": bbox,
        "note": "stub crop",
    }


@weave.op()
def subcall(task: str, state: AgentState, events: list[str]) -> str:
    """Recursively call step with a subtask, with context compression for ultralong tasks."""
    # For recursive subcalls, compress parent context to avoid token bloat
    # Keep only relevant events for the subtask
    compressed_events = events.copy()
    
    # If we have many events, keep only:
    # 1. Recent events (last 5)
    # 2. Events relevant to the subtask (if we had semantic search)
    # 3. Important milestones
    if len(events) > 20:
        # Keep recent events and compress older ones
        recent = events[-5:]
        # For now, just use recent events for subcalls
        # TODO: Add semantic retrieval to find relevant past events
        compressed_events = recent
        compressed_events.insert(0, f"[compressed_context] Parent goal: {state.goal}")
    
    # Create subcall with compressed context
    next_state = AgentState(goal=task, depth=state.depth + 1, max_depth=state.max_depth)
    result = step(next_state, compressed_events)
    
    # Compress subcall result when returning
    result_summary = f"subcall:{task}:{result.type}"
    if result.type == "done":
        result_summary += f":{result.payload.get('reason', '')[:50]}"
    
    return result_summary


@weave.op()
def step(
    state: AgentState,
    events: list[str],
    observation: dict[str, Any] | None = None,
    context_examiner: RLMContextExaminer | None = None,
) -> Action:
    """Plan and execute the next step using GPT-4o with vision and RLM context examination."""
    # Add step event
    events.append(f"step:{state.step_count}:{state.goal}")
    
    # RLM: Examine long context programmatically if we have many events
    context_summary = ""
    if len(events) > 20 and context_examiner:
        # Use RLM pattern: examine context as external environment
        full_context = "\n".join(events)
        examination = context_examiner.examine(
            context=full_context,
            query=f"What is relevant to achieving: {state.goal}?",
            goal=state.goal,
        )
        if isinstance(examination, dict):
            context_summary = examination.get("summary", "") or examination.get("combined_content", "")
        else:
            context_summary = str(examination)
        events.append(f"rlm_examination:{state.step_count}:{context_summary[:100]}")
    
    # Extract screenshot if available
    screenshot_base64 = None
    if observation:
        screenshot_base64 = observation.get("screenshot_base64")
        
        # RLM for Vision: Examine screenshot in snippets if available
        visual_examiner = None
        if screenshot_base64 and len(screenshot_base64) > 50000:  # Large screenshot
            # Use visual RLM: divide screenshot into snippets and examine programmatically
            visual_examiner = VisualRLMExaminer(grid_size=(3, 3))
            visual_analysis = visual_examiner.examine_screenshot(
                screenshot_base64=screenshot_base64,
                query=f"What is relevant to: {state.goal}?",
                goal=state.goal,
            )
            events.append(f"visual_rlm:{state.step_count}:{visual_analysis.get('combined_description', '')[:100]}")
            # Use visual RLM findings for planning
            screenshot_base64 = None  # Don't send full screenshot, use RLM summary
        elif screenshot_base64:
            # Small screenshot - analyze directly
            analysis = analyze_observation(
                goal=state.goal,
                screenshot_base64=screenshot_base64,
                url=observation.get("url"),
            )
            events.append(f"analysis:{state.step_count}:{analysis.get('description', '')[:100]}")
    
    # Use adaptive context: if we have RLM summary, use it; otherwise use recent events
    history_for_planning = events
    if context_summary:
        # Use RLM-examined context + recent events
        history_for_planning = [context_summary] + events[-10:]
    
    # Use GPT-4o to plan next action with vision
    plan = plan_next_action(
        goal=state.goal,
        observation=observation,
        history=history_for_planning,
        depth=state.depth,
        screenshot_base64=screenshot_base64,
    )
    
    action_type = plan.get("action_type", "act")
    reasoning = plan.get("reasoning", "")
    
    # Add plan event
    events.append(f"plan:{state.step_count}:{reasoning}")
    
    # Build action payload based on plan
    payload: dict[str, Any] = {"reasoning": reasoning}
    
    if action_type == "subcall":
        task = plan.get("task", f"subtask for: {state.goal}")
        payload["task"] = task
        return Action(type="subcall", payload=payload)
    
    elif action_type == "done":
        reason = plan.get("reasoning", "Task complete")
        payload["reason"] = reason
        return Action(type="done", payload=payload)
    
    else:  # act
        command = plan.get("command", "observe")
        payload["command"] = command
        if plan.get("target"):
            payload["target"] = plan["target"]
        if plan.get("text"):
            payload["text"] = plan["text"]
        return Action(type="act", payload=payload)


@weave.op()
def score(trajectory: list[Action]) -> dict[str, Any]:
    success = any(action.type == "done" for action in trajectory)
    return {
        "success": success,
        "steps": len(trajectory),
    }


def run_agent(
    goal: str,
    driver: WebDriver,
    workspace: Workspace,
    enable_multi_agent: bool = False,
) -> dict[str, Any]:
    state = AgentState(goal=goal)
    trajectory: list[Action] = []
    observation: Observation | None = None

    # Initialize RLM context examiner
    context_examiner = RLMContextExaminer(chunk_size=1000, overlap=200)

    # Initialize multi-agent coordinator if enabled
    coordinator = None
    if enable_multi_agent:
        coordinator = MultiAgentCoordinator()
        print("[INFO] Multi-agent coordination enabled")

    # Get events list from workspace
    events = workspace.get("events", [])

    # Initial observation
    observation = driver.observe()
    events.append(f"observe:{observation.url}")
    workspace.set("events", events)

    for _ in range(30):  # Increased max steps for complex multi-step tasks
        # Convert observation to dict for Weave
        obs_dict = None
        if observation:
            obs_dict = {
                "url": observation.url,
                "screenshot_path": observation.screenshot_path,
                "screenshot_base64": observation.screenshot_base64,
                "metadata": observation.metadata or {},
            }
        
        # Get fresh events list
        events = workspace.get("events", [])
        action = step(state, events, obs_dict, context_examiner)
        trajectory.append(action)
        
        if action.type == "subcall":
            task = action.payload["task"]
            result = subcall(task, state, events)
            events.append(f"subcall_result:{result}")
            workspace.set("events", events)
        
        elif action.type == "act":
            command = action.payload.get("command", "observe")
            
            if command == "observe":
                observation = driver.observe()
                events.append(f"observe:{observation.url}")
                workspace.set("events", events)
            else:
                # Execute the action
                driver.act(action)
                events.append(f"act:{command}:{action.payload.get('target', '')}")
                # Observe after action
                observation = driver.observe()
                events.append(f"observe_after:{observation.url}")
                workspace.set("events", events)
        
        elif action.type == "done":
            events.append(f"done:{action.payload.get('reason', '')}")
            workspace.set("events", events)
            
            # If multi-agent enabled, delegate follow-up tasks
            if coordinator and action.payload.get("delegate_followup"):
                followup_tasks = action.payload.get("followup_tasks", [])
                for task in followup_tasks:
                    result = coordinator.delegate_task(
                        task=task.get("task", ""),
                        required_capabilities=task.get("capabilities", []),
                        context=task.get("context", {}),
                    )
                    events.append(f"delegated:{task.get('task', '')}:{result.get('status', 'unknown')}")
                    workspace.set("events", events)
            
            break
        
        state.step_count += 1

    final_events = workspace.get("events", [])
    return {
        "trajectory": trajectory,
        "score": score(trajectory),
        "events": final_events,
        "last_observation": observation,
    }
