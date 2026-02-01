# Vercel Deployment Setup

## Setting Environment Variables in Vercel

For the webapp to automatically use your credentials without asking users, you need to set environment variables in your Vercel project:

1. Go to your Vercel project dashboard: https://vercel.com/dashboard
2. Select your `weavehack3` project
3. Go to **Settings** → **Environment Variables**
4. Add the following variables:

### Required Variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `WANDB_API_KEY` - Your Weights & Biases API key
- `WANDB_PROJECT` - Your W&B project name (e.g., `weavehacks-rvla`)
- `WANDB_ENTITY` - Your W&B entity/username

### Optional Variables:
- `REDIS_URL` - Redis connection URL (if using external memory)
- `BROWSERBASE_API_KEY` - Browserbase API key
- `BROWSERBASE_PROJECT_ID` - Browserbase project ID

5. After adding variables, **redeploy** your application for changes to take effect.

## Adding Images

The webapp expects two image files in the `web/public/` directory:

1. **lobsterpot-logo.png** - The Lobster Pot logo
2. **fisherman-background.jpg** - The background image of the fisherman with lobster

To add them:
1. Place the image files in `web/public/`
2. Commit and push to GitHub
3. Vercel will automatically redeploy

The app will work without these images (showing fallbacks), but adding them completes the design.
