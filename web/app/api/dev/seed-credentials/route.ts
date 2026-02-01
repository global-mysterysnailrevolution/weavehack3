import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function GET() {
  // Always use private environment variables (server-side only)
  // These are set in Vercel project settings and are never exposed to the client
  // The client receives the values but they're not in the bundle
  const credentials = {
    openai_api_key: process.env.OPENAI_API_KEY || '',
    wandb_api_key: process.env.WANDB_API_KEY || '',
    wandb_project: process.env.WANDB_PROJECT || process.env.NEXT_PUBLIC_WANDB_PROJECT || 'weavehacks-rvla',
    wandb_entity: process.env.WANDB_ENTITY || process.env.NEXT_PUBLIC_WANDB_ENTITY || '',
    redis_url: process.env.REDIS_URL || '',
    browserbase_api_key: process.env.BROWSERBASE_API_KEY || '',
    browserbase_project_id: process.env.BROWSERBASE_PROJECT_ID || '',
  };

  // Don't log credentials in production for security
  if (process.env.NODE_ENV !== 'production') {
    console.log('🔐 Loading credentials from environment variables:', {
      hasOpenAI: !!credentials.openai_api_key,
      hasWandb: !!credentials.wandb_api_key,
      hasProject: !!credentials.wandb_project,
      hasBrowserbase: !!credentials.browserbase_api_key,
    });
  }

  return NextResponse.json(credentials);
}
