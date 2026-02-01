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
    if process.stdout:
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            output_lines.append(line)
            try:
                parsed = json.loads(line)
                payload = {"type": "openclaw_event", "mode": mode, "payload": parsed}
            except Exception:
                payload = {"type": "openclaw_log", "mode": mode, "message": line}
            yield f"data: {json.dumps(payload)}\n\n"

    process.wait()
    exit_code = process.returncode

    tail = output_lines[-20:]
    record_openclaw_run(mode=mode, goal=goal, iteration=iteration, exit_code=exit_code, output_tail=tail)
    _save_beach_state(
        {
            "last_mode": mode,
            "last_goal": goal,
            "last_iteration": iteration,
            "last_output_tail": tail,
        }
    )

    yield f"data: {json.dumps({'type': 'openclaw_complete', 'mode': mode, 'exit_code': exit_code})}\n\n"


@weave.op()
def record_openclaw_run(
    mode: str,
    goal: str,
    iteration: int,
    exit_code: int | None,
    output_tail: list[str],
) -> dict:
    return {
        "mode": mode,
        "goal": goal,
        "iteration": iteration,
        "exit_code": exit_code,
        "output_tail": output_tail,
    }


@app.post("/api/openclaw/beach")
async def openclaw_beach(request: OpenClawRequest):
    state = _load_beach_state()
    goal = request.goal
    if request.iteration > 0 and state.get("last_output_tail"):
        tail = "\n".join(state.get("last_output_tail", []))
        goal = f"{goal}\n\nPrevious beach notes:\n{tail}"

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
