# Deployment Guide

## Quick Deploy to Vercel

### Frontend (Web UI)

1. **Push to GitHub** (already done ✅)

2. **Deploy to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Click "Import Project"
   - Select your GitHub repository
   - Set root directory to `web`
   - Deploy!

3. **Environment Variables** (Optional):
   - Users can input credentials via the UI
   - Or set defaults in Vercel dashboard

### Backend (Python API)

For production, you need to run the Python backend. Options:

#### Option 1: Railway (Recommended for Python)

1. Go to [railway.app](https://railway.app)
2. Create new project from GitHub repo
3. Add Python service
4. Set start command: `python -m uvicorn api:app --host 0.0.0.0 --port $PORT`
5. Update `web/next.config.js` to point to Railway URL

#### Option 2: Render

1. Go to [render.com](https://render.com)
2. Create new Web Service
3. Connect GitHub repo
4. Set build command: `pip install -e . && pip install fastapi uvicorn`
5. Set start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`

#### Option 3: Fly.io

```bash
fly launch
fly deploy
```

## Full-Stack Setup

### Create FastAPI Backend

Create `api/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    goal: str
    credentials: dict

@app.post("/api/agent/run")
async def run_agent(request: AgentRequest):
    # Run agent and stream updates
    process = subprocess.Popen(
        ["python", "src/rvla/api_server.py", request.goal],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, **request.credentials}
    )
    
    async def generate():
        for line in process.stdout:
            if line.startswith(b"UPDATE:"):
                yield f"data: {line[7:].decode()}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Local Development

### Start Backend

```bash
# Terminal 1: Python backend
cd C:\Users\globa\weavehack3
python -m uvicorn api.main:app --reload --port 8000
```

### Start Frontend

```bash
# Terminal 2: Next.js frontend
cd C:\Users\globa\weavehack3\web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Environment Setup

Users can input credentials via the UI, or set environment variables:

```bash
OPENAI_API_KEY=sk-...
WANDB_API_KEY=...
WANDB_PROJECT=weavehacks-rvla
WANDB_ENTITY=your-username
REDIS_URL=redis://...
BROWSERBASE_API_KEY=bb_...
BROWSERBASE_PROJECT_ID=...
```

## Demo Checklist

- [x] Web UI with real-time updates
- [x] Credential input form
- [x] Screenshot viewer
- [x] Action history
- [x] RLM visualization
- [x] Weave trace links
- [ ] Backend API integration
- [ ] Vercel deployment
- [ ] Railway/Render backend
