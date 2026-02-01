# RLM-VLA Web UI

Modern web interface for the RLM-VLA agent, built with Next.js and Tailwind CSS.

## Features

- 🎯 **Goal Input**: Enter agent goals through an intuitive interface
- 📊 **Real-time Execution**: Watch the agent execute tasks in real-time
- 📸 **Screenshot Viewer**: See what the agent sees as it navigates
- 📝 **Action History**: Track all actions taken by the agent
- 🔍 **RLM Visualization**: See recursive context examination in action
- 📈 **Weave Integration**: Direct links to Weave trace visualizations
- 🔐 **Secure Credentials**: Store API keys securely in browser localStorage

## Development

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Import project in Vercel
3. Set environment variables (optional - users can input via UI)
4. Deploy!

The UI will work with a Python backend API server. For production, you'll need to:
- Deploy the Python backend separately (e.g., Railway, Render, Fly.io)
- Update the API endpoint in `next.config.js`

### Alternative: Full-stack on Vercel

You can also use Vercel's serverless functions to run the Python agent directly, though this requires additional setup.

## Architecture

```
Frontend (Next.js)
  ↓ HTTP/SSE
Backend API (Python FastAPI/Flask)
  ↓
RLM-VLA Agent
  ↓
Weave Tracing → W&B Dashboard
```

## Environment Variables

Users can input credentials via the UI, or you can set defaults:

- `OPENAI_API_KEY`
- `WANDB_API_KEY`
- `WANDB_PROJECT`
- `WANDB_ENTITY`
- `REDIS_URL`
- `BROWSERBASE_API_KEY`
- `BROWSERBASE_PROJECT_ID`
