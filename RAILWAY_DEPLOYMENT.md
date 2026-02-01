# Railway Deployment Guide

## Quick Deploy to Railway

Railway is perfect for full-stack apps with both frontend and backend!

### Option 1: Deploy Frontend Only (Simplest)

1. **Go to Railway**: [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub repo**
3. **Select your repo**: `global-mysterysnailrevolution/weavehack3`
4. **Configure**:
   - **Root Directory**: `web`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
5. **Add Environment Variables** (optional - users can input via UI):
   - `BACKEND_URL` (if deploying backend separately)
6. **Deploy!**

### Option 2: Deploy Full-Stack (Frontend + Backend)

Railway supports multiple services. Deploy both:

#### Service 1: Frontend (Next.js)

1. **New Service** → **GitHub Repo**
2. **Settings**:
   - **Root Directory**: `web`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
   - **Port**: Railway auto-assigns (Next.js uses `PORT` env var)

#### Service 2: Backend (Python FastAPI)

1. **New Service** → **GitHub Repo** (same repo)
2. **Settings**:
   - **Root Directory**: `.` (root)
   - **Build Command**: `pip install -e . && pip install fastapi uvicorn`
   - **Start Command**: `python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Port**: Railway auto-assigns

3. **Connect Services**:
   - In Frontend service, add environment variable:
     - `BACKEND_URL` = `https://your-backend-service.railway.app`
   - Or use Railway's service discovery (automatic)

#### Service Discovery (Recommended)

Railway automatically provides service URLs via environment variables:
- `RAILWAY_PUBLIC_DOMAIN` - Public domain for the service
- Other services are accessible via internal networking

Update `web/next.config.js` to use Railway's service discovery:

```javascript
const backendUrl = process.env.RAILWAY_SERVICE_URL || 
                   process.env.BACKEND_URL || 
                   'http://localhost:8000';
```

### Option 3: Monorepo with Nixpacks (Advanced)

Railway can detect and build both services automatically using `nixpacks.toml`:

1. **New Project** → **GitHub Repo**
2. Railway will detect `nixpacks.toml` and build accordingly
3. Configure services in Railway dashboard

## Environment Variables

Set these in Railway dashboard (or let users input via UI):

### Frontend Service
- `BACKEND_URL` - URL of backend service (if separate)
- `NEXT_PUBLIC_APP_URL` - Public URL of frontend (optional)

### Backend Service
- `OPENAI_API_KEY` - OpenAI API key
- `WANDB_API_KEY` - Weights & Biases API key
- `WANDB_PROJECT` - W&B project name
- `WANDB_ENTITY` - W&B entity/username
- `REDIS_URL` - Redis connection URL (optional)
- `BROWSERBASE_API_KEY` - Browserbase API key (optional)
- `BROWSERBASE_PROJECT_ID` - Browserbase project ID (optional)

## Local Testing

Test the full stack locally:

```bash
# Terminal 1: Backend
python -m uvicorn api.main:app --reload --port 8000

# Terminal 2: Frontend
cd web
npm install
npm run dev
```

## Railway-Specific Features

### Automatic HTTPS
Railway provides HTTPS automatically for all services.

### Custom Domains
1. Go to service settings
2. Add custom domain
3. Railway handles SSL certificates

### Logs
View real-time logs in Railway dashboard.

### Metrics
Railway provides CPU, memory, and network metrics.

## Troubleshooting

### Build Fails
- Check build logs in Railway dashboard
- Ensure all dependencies are in `package.json` (frontend) or `pyproject.toml` (backend)

### Backend Not Connecting
- Verify `BACKEND_URL` environment variable
- Check backend service is running
- Use Railway's internal service URLs for service-to-service communication

### Port Issues
- Railway assigns `$PORT` automatically
- Next.js and FastAPI both respect `PORT` environment variable

## Cost

Railway offers:
- **Free tier**: $5 credit/month
- **Hobby**: $5/month for 1 service
- **Pro**: $20/month for unlimited services

Perfect for hackathon demos! 🚀
