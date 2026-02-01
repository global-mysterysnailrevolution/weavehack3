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


@app.post("/api/agent/run")
async def run_agent(request: AgentRequest):
    """Run the agent and stream updates via Server-Sent Events."""
    
    # Set environment variables from credentials
    env = os.environ.copy()
    for key, value in request.credentials.items():
        if value:
            env[key.upper()] = str(value)
    
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
    lower = "\n".join(output_lines).lower()
    error_hits = sum(token in lower for token in ["error", "failed", "exception", "traceback"])
    success_hits = sum(token in lower for token in ["complete", "completed", "success", "done"])
    pricing_hits = sum(
        token in lower
        for token in [
            "shopbiolinkdepot",
            "biolink",
            "pricing",
            "price",
            "google",
            "images",
            "compare",
            "vendor",
        ]
    )

    score = 0.5
    score += min(0.3, success_hits * 0.1)
    score += min(0.2, pricing_hits * 0.05)
    score -= min(0.4, error_hits * 0.15)
    score = max(0.0, min(1.0, score))

    suggestions: list[str] = []
    if "shopbiolinkdepot" not in lower:
        suggestions.append("Include the exact shopbiolinkdepot product names and URLs.")
    if "google" not in lower:
        suggestions.append("Add explicit web search steps (Google/Bing) for each product.")
    if "image" not in lower and "compare" not in lower:
        suggestions.append("Compare product images to confirm the correct item.")
    if "price" not in lower and "pricing" not in lower:
        suggestions.append("Extract price from reputable vendor pages, not marketplaces.")
    if error_hits > 0:
        suggestions.append("Add recovery steps for errors and retry navigation.")

    return {
        "score": round(score, 2),
        "error_hits": error_hits,
        "success_hits": success_hits,
        "pricing_hits": pricing_hits,
        "suggestions": suggestions,
    }


def _stream_openclaw(
    mode: str,
    goal: str,
    iteration: int,
) -> Iterable[str]:
    env = os.environ.copy()
    env["OPENCLAW_SANDBOX"] = "1" if mode == "beach" else "0"

    base_cmd = os.getenv(
        "OPENCLAW_BEACH_CMD" if mode == "beach" else "OPENCLAW_SEA_CMD",
        "openclaw agent --message",
    )
    cmd = _build_openclaw_cmd(base_cmd, goal)

    yield f"data: {json.dumps({'type': 'openclaw_start', 'mode': mode, 'goal': goal, 'iteration': iteration})}\n\n"

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            text=True,
            bufsize=1,
            shell=True,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'error': str(exc)})}\n\n"
        return

    output_lines: list[str] = []
    events: list[dict] = []
    if process.stdout:
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            output_lines.append(line)
            try:
                parsed = json.loads(line)
                events.append(parsed)
                if len(events) > OPENCLAW_EVENT_LIMIT:
                    events.pop(0)
                payload = {"type": "openclaw_event", "mode": mode, "payload": parsed}
            except Exception:
                payload = {"type": "openclaw_log", "mode": mode, "message": line}
            yield f"data: {json.dumps(payload)}\n\n"

    process.wait()
    exit_code = process.returncode

    tail = output_lines[-50:]
    analysis = _analyze_openclaw_output(output_lines)
    record_openclaw_run(
        mode=mode,
        goal=goal,
        iteration=iteration,
        exit_code=exit_code,
        output_tail=tail,
        events=events,
        analysis=analysis,
    )
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
    return StreamingResponse(
        _stream_openclaw("sea", request.goal, request.iteration),
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
