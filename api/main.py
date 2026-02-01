"""FastAPI backend for RLM-VLA agent web UI."""

import os
import subprocess
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
