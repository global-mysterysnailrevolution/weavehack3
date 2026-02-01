"""FastAPI backend for RLM-VLA agent web UI."""

import os
import subprocess
import json
import shlex
from typing import Optional, Iterable
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import weave
from rvla.weave_init import ensure_weave_init
from rvla.prompt_database import get_prompt_database, LearnedPrompt

ensure_weave_init()
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="RLM-VLA Agent API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    goal: str
    credentials: dict


class OpenClawRequest(BaseModel):
    goal: str
    iteration: int = 0


@app.get("/")
async def root():
    return {"message": "RLM-VLA Agent API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/prompts")
async def list_prompts(
    task_type: Optional[str] = None,
    limit: int = 10,
):
    """List stored learned prompts, optionally filtered by task type."""
    try:
        prompt_db = get_prompt_database()
        
        if task_type:
            # Get prompts by task type
            pattern = prompt_db._key("*")
            keys = prompt_db._get_all_keys(pattern)
            prompts = []
            for key in keys:
                prompt_id = key.replace("prompt:db:", "")
                prompt = prompt_db.get_prompt(prompt_id)
                if prompt and prompt.task_type == task_type:
                    prompts.append({
                        "prompt_id": prompt.prompt_id,
                        "task_type": prompt.task_type,
                        "task_context": prompt.task_context[:200],
                        "success_rate": prompt.success_rate,
                        "usage_count": prompt.usage_count,
                        "created_at": prompt.created_at,
                        "problem_patterns": [
                            {
                                "problem_type": pp.problem_type,
                                "frequency": pp.frequency,
                            }
                            for pp in prompt.problem_patterns
                        ],
                    })
            prompts.sort(key=lambda x: x["success_rate"], reverse=True)
            return {"prompts": prompts[:limit], "count": len(prompts)}
        else:
            # Get all prompts
            pattern = prompt_db._key("*")
            keys = prompt_db._get_all_keys(pattern)
            prompts = []
            for key in keys[:limit * 2]:  # Get more to filter
                prompt_id = key.replace("prompt:db:", "")
                prompt = prompt_db.get_prompt(prompt_id)
                if prompt:
                    prompts.append({
                        "prompt_id": prompt.prompt_id,
                        "task_type": prompt.task_type,
                        "task_context": prompt.task_context[:200],
                        "success_rate": prompt.success_rate,
                        "usage_count": prompt.usage_count,
                        "created_at": prompt.created_at,
                    })
            prompts.sort(key=lambda x: x["success_rate"], reverse=True)
            return {"prompts": prompts[:limit], "count": len(prompts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list prompts: {str(e)}")


@app.post("/api/agent/run")
async def run_agent(request: AgentRequest):
    """Run the agent and stream updates via Server-Sent Events."""
    
    # Use environment variables first (private), then fall back to request credentials
    env = os.environ.copy()
    
    # Map credential keys to environment variable names
    env_var_map = {
        'openai_api_key': 'OPENAI_API_KEY',
        'wandb_api_key': 'WANDB_API_KEY',
        'wandb_project': 'WANDB_PROJECT',
        'wandb_entity': 'WANDB_ENTITY',
        'redis_url': 'REDIS_URL',
        'browserbase_api_key': 'BROWSERBASE_API_KEY',
        'browserbase_project_id': 'BROWSERBASE_PROJECT_ID',
    }
    
    # Prioritize environment variables, use request credentials as fallback
    for cred_key, env_key in env_var_map.items():
        # Use env var if available, otherwise use request credential
        env_value = os.getenv(env_key) or request.credentials.get(cred_key, '')
        if env_value:
            env[env_key] = str(env_value)
    
    # Path to the API server script
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "src", "rvla", "api_server.py"
    )
    
    if not os.path.exists(script_path):
        raise HTTPException(
            status_code=500,
            detail=f"Agent script not found at {script_path}"
        )
    
    async def generate():
        """Generate SSE events from the agent process."""
        try:
            # Start the Python agent process
            process = subprocess.Popen(
                ["python", script_path, request.goal],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=os.path.dirname(os.path.dirname(__file__)),
                text=True,
                bufsize=1,
            )
            
            # Stream stdout line by line
            for line in process.stdout:
                if line.startswith("UPDATE:"):
                    # Extract JSON from UPDATE: prefix
                    update_json = line[7:].strip()
                    yield f"data: {update_json}\n\n"
            
            # Wait for process to complete
            process.wait()
            
            if process.returncode != 0:
                stderr_output = process.stderr.read() if process.stderr else ""
                yield f"data: {json.dumps({'type': 'error', 'error': f'Process failed: {stderr_output}'})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


BEACH_STATE_PATH = os.getenv("LOBSTERPOT_BEACH_STATE_PATH", ".beach_state.json")
OPENCLAW_EVENT_LIMIT = int(os.getenv("LOBSTERPOT_OPENCLAW_EVENT_LIMIT", "500"))


def _load_beach_state() -> dict:
    try:
        with open(BEACH_STATE_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def _save_beach_state(state: dict) -> None:
    try:
        with open(BEACH_STATE_PATH, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
    except Exception:
        pass


def _build_openclaw_cmd(base_cmd: str, goal: str) -> list[str]:
    parts = shlex.split(base_cmd, posix=False)
    return parts + [goal]


def _analyze_openclaw_output(output_lines: list[str]) -> dict:
    """Analyze OpenClaw output for pricing extraction tasks and generate improvement suggestions."""
    full_output = "\n".join(output_lines)
    lower = full_output.lower()
    
    # Error detection
    error_hits = sum(token in lower for token in ["error", "failed", "exception", "traceback", "timeout"])
    
    # Success indicators
    success_hits = sum(token in lower for token in [
        "complete", "completed", "success", "done", "finished",
        "saved", "extracted", "found", "verified"
    ])
    
    # Pricing task specific keywords
    pricing_keywords = [
        "shopbiolinkdepot", "biolink", "pricing", "price", "$", "usd",
        "product", "item", "cost", "retail"
    ]
    pricing_hits = sum(token in lower for token in pricing_keywords)
    
    # Web search indicators
    search_hits = sum(token in lower for token in [
        "google", "search", "bing", "query", "results"
    ])
    
    # Image/screenshot indicators
    image_hits = sum(token in lower for token in [
        "screenshot", "image", "photo", "picture", "compare", "visual"
    ])
    
    # Documentation indicators
    doc_hits = sum(token in lower for token in [
        "json", "file", "save", "document", "report", "output", "data"
    ])
    
    # Vendor verification indicators
    vendor_hits = sum(token in lower for token in [
        "vendor", "ebay", "amazon", "marketplace", "legitimate", "retailer"
    ])
    
    # Calculate base score
    score = 0.3  # Start lower to encourage improvement
    
    # Success bonus
    score += min(0.2, success_hits * 0.05)
    
    # Task-specific bonuses
    score += min(0.15, pricing_hits * 0.02)  # Pricing keywords
    score += min(0.15, search_hits * 0.05)    # Web search
    score += min(0.1, image_hits * 0.05)      # Screenshots/images
    score += min(0.1, doc_hits * 0.05)        # Documentation
    score += min(0.1, vendor_hits * 0.05)     # Vendor verification
    
    # Error penalty
    score -= min(0.4, error_hits * 0.15)
    
    score = max(0.0, min(1.0, score))
    
    # Generate specific suggestions
    suggestions: list[str] = []
    
    if "shopbiolinkdepot" not in lower and "biolink" not in lower:
        suggestions.append("Include the exact shopbiolinkdepot product names and URLs.")
    
    if search_hits == 0:
        suggestions.append("Add explicit web search steps (Google/Bing) for each product.")
    elif search_hits < 2:
        suggestions.append("Perform web searches for each product individually, not just one search.")
    
    if image_hits == 0:
        suggestions.append("Take screenshots of product pages showing prices and compare product images.")
    elif "compare" not in lower:
        suggestions.append("Compare product images from Google results to confirm it's the same item.")
    
    if "price" not in lower and "pricing" not in lower:
        suggestions.append("Extract and document prices from both shopbiolinkdepot and market sources.")
    elif "difference" not in lower and "compare" not in lower:
        suggestions.append("Calculate and document the price difference between shopbiolinkdepot and market prices.")
    
    if vendor_hits == 0:
        suggestions.append("Identify if items are only on eBay or from legitimate vendors.")
    
    if doc_hits == 0:
        suggestions.append("Save findings to a structured JSON file with product details and pricing comparisons.")
    elif "json" not in lower:
        suggestions.append("Ensure output is saved in structured JSON format as specified.")
    
    if "screenshot" not in lower and "image" not in lower:
        suggestions.append("Take screenshots of product pages showing prices for verification.")
    
    if error_hits > 0:
        suggestions.append("Add error recovery steps and retry navigation if pages fail to load.")
    
    # Check for completeness
    if pricing_hits > 0 and search_hits > 0 and image_hits > 0 and doc_hits > 0:
        if score < 0.8:
            suggestions.append("Review output structure - all components present but may need refinement.")
    
    return {
        "score": round(score, 2),
        "error_hits": error_hits,
        "success_hits": success_hits,
        "pricing_hits": pricing_hits,
        "search_hits": search_hits,
        "image_hits": image_hits,
        "doc_hits": doc_hits,
        "vendor_hits": vendor_hits,
        "suggestions": suggestions,
    }


def _stream_openclaw(
    mode: str,
    goal: str,
    iteration: int,
) -> Iterable[str]:
    """Run the RLM-VLA agent (not OpenClaw - that doesn't exist).
    
    This uses the actual RLM-VLA agent from src/rvla/agent.py.
    'beach' mode = sandboxed/test mode (same as regular, just labeled differently)
    'sea' mode = production mode (same as regular)
    """
    from rvla.agent import run_agent
    from rvla.memory import workspace_from_env
    from rvla.web import WebDriver
    
    yield f"data: {json.dumps({'type': 'openclaw_start', 'mode': mode, 'goal': goal, 'iteration': iteration})}\n\n"
    
    output_lines: list[str] = []
    events: list[dict] = []
    exit_code = 0
    driver = None
    
    try:
        # Initialize components
        workspace = workspace_from_env()
        driver = WebDriver()
        
        yield f"data: {json.dumps({'type': 'openclaw_log', 'mode': mode, 'message': f'[RLM-VLA Agent] Starting task: {goal[:100]}...'})}\n\n"
        output_lines.append(f"Starting RLM-VLA agent task: {goal}")
        
        # Run agent
        result = run_agent(
            goal=goal,
            driver=driver,
            workspace=workspace,
            enable_multi_agent=True,
        )
        
        # Stream trajectory as events
        trajectory = result.get('trajectory', [])
        for i, action in enumerate(trajectory):
            event_data = {
                "type": "openclaw_event",
                "mode": mode,
                "payload": {
                    "step": i + 1,
                    "action_type": action.type,
                    "action_payload": action.payload,
                },
                "line_number": i + 1,
            }
            events.append(event_data["payload"])
            if len(events) > OPENCLAW_EVENT_LIMIT:
                events.pop(0)
            
            action_desc = action.payload.get('command', action.payload.get('reasoning', action.payload.get('task', '')))
            log_msg = f"[Step {i+1}] {action.type}: {str(action_desc)[:100]}"
            output_lines.append(log_msg)
            yield f"data: {json.dumps(event_data)}\n\n"
            yield f"data: {json.dumps({'type': 'openclaw_log', 'mode': mode, 'message': log_msg})}\n\n"
        
        # Add final events
        for event in result.get('events', []):
            output_lines.append(f"Event: {event}")
            events.append({"event": event})
        
        # Calculate score from result
        score_result = result.get('score', {})
        if isinstance(score_result, dict):
            success = score_result.get('success', False)
            steps = score_result.get('steps', len(trajectory))
        else:
            success = bool(score_result) if score_result else False
            steps = len(trajectory)
        
        output_lines.append(f"Task completed. Success: {success}, Steps: {steps}")
        
    except Exception as exc:
        exit_code = 1
        error_msg = f"Error running agent: {str(exc)}"
        output_lines.append(error_msg)
        yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
        import traceback
        output_lines.append(traceback.format_exc())
    finally:
        if driver:
            try:
                driver.close()
            except:
                pass
    
    # Analyze output and record
    tail = output_lines[-50:]
    analysis = _analyze_openclaw_output(output_lines)
    
    # Record to Weave
    record_openclaw_run(
        mode=mode,
        goal=goal,
        iteration=iteration,
        exit_code=exit_code,
        output_tail=tail,
        events=events,
        analysis=analysis,
    )
    
    # Store learned prompt in Redis database if this was a successful improvement
    if mode == "beach" and iteration > 0 and analysis.get("score", 0) > 0.7:
        try:
            prompt_db = get_prompt_database()
            # Extract original goal (before suggestions were added)
            original_goal = goal.split("\n\nPrevious beach notes:")[0].strip()
            if "\n\nLEARNED PROMPT TOOL" in original_goal:
                original_goal = original_goal.split("\n\nLEARNED PROMPT TOOL")[0].strip()
            
            # Create improved prompt (goal with suggestions incorporated)
            improved_prompt = goal
            
            # Determine task type from goal
            task_type = "pricing_extraction" if "shopbiolinkdepot" in goal.lower() or "pricing" in goal.lower() else "general"
            
            # Prepare trace data for pattern extraction
            trace_data = {
                "events": events,
                "output_tail": tail,
                "analysis": analysis,
                "goal": original_goal,
            }
            
            # Create and store learned prompt
            learned_prompt = prompt_db.create_learned_prompt(
                original_prompt=original_goal,
                improved_prompt=improved_prompt,
                analysis=analysis,
                goal=original_goal,
                task_type=task_type,
                metadata={
                    "mode": mode,
                    "iteration": iteration,
                    "exit_code": exit_code,
                    "suggestions": analysis.get("suggestions", []),
                },
                trace_data=trace_data,
            )
            prompt_db.store_prompt(learned_prompt)
            yield f"data: {json.dumps({'type': 'prompt_stored', 'prompt_id': learned_prompt.prompt_id, 'task_type': task_type})}\n\n"
        except Exception as e:
            # Don't fail the whole request if prompt storage fails
            print(f"[WARN] Failed to store learned prompt: {e}")
    
    _save_beach_state(
        {
            "last_mode": mode,
            "last_goal": goal,
            "last_iteration": iteration,
            "last_output_tail": tail,
            "last_analysis": analysis,
        }
    )

    yield f"data: {json.dumps({'type': 'openclaw_score', 'mode': mode, 'score': analysis['score']})}\n\n"
    yield f"data: {json.dumps({'type': 'openclaw_suggestions', 'mode': mode, 'suggestions': analysis['suggestions']})}\n\n"
    yield f"data: {json.dumps({'type': 'openclaw_complete', 'mode': mode, 'exit_code': exit_code})}\n\n"


@weave.op()
def record_openclaw_run(
    mode: str,
    goal: str,
    iteration: int,
    exit_code: int | None,
    output_tail: list[str],
    events: list[dict],
    analysis: dict,
) -> dict:
    return {
        "mode": mode,
        "goal": goal,
        "iteration": iteration,
        "exit_code": exit_code,
        "output_tail": output_tail,
        "events": events,
        "analysis": analysis,
    }


@app.post("/api/openclaw/beach")
async def openclaw_beach(request: OpenClawRequest):
    state = _load_beach_state()
    goal = request.goal
    
    # Try to retrieve relevant learned prompts from Redis database
    try:
        prompt_db = get_prompt_database()
        task_type = "pricing_extraction" if "shopbiolinkdepot" in goal.lower() or "pricing" in goal.lower() else "general"
        learned_prompt_tool = prompt_db.get_prompt_tool_for_openclaw(
            task_context=goal,
            task_type=task_type,
        )
        if learned_prompt_tool:
            goal = f"{goal}\n\n{learned_prompt_tool}"
    except Exception as e:
        print(f"[WARN] Failed to retrieve learned prompts: {e}")
    
    # Add previous iteration feedback if available
    if request.iteration > 0 and state.get("last_output_tail"):
        tail = "\n".join(state.get("last_output_tail", []))
        suggestion_lines = []
        last_analysis = state.get("last_analysis") or {}
        for item in last_analysis.get("suggestions", []):
            suggestion_lines.append(f"- {item}")
        suggestions = "\n".join(suggestion_lines)
        goal = f"{goal}\n\nPrevious beach notes:\n{tail}"
        if suggestions:
            goal += f"\n\nPatch suggestions:\n{suggestions}"

    return StreamingResponse(
        _stream_openclaw("beach", goal, request.iteration),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/openclaw/sea")
async def openclaw_sea(request: OpenClawRequest):
    goal = request.goal
    
    # Try to retrieve relevant learned prompts from Redis database
    try:
        prompt_db = get_prompt_database()
        task_type = "pricing_extraction" if "shopbiolinkdepot" in goal.lower() or "pricing" in goal.lower() else "general"
        learned_prompt_tool = prompt_db.get_prompt_tool_for_openclaw(
            task_context=goal,
            task_type=task_type,
        )
        if learned_prompt_tool:
            goal = f"{goal}\n\n{learned_prompt_tool}"
    except Exception as e:
        print(f"[WARN] Failed to retrieve learned prompts: {e}")
    
    return StreamingResponse(
        _stream_openclaw("sea", goal, request.iteration),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
