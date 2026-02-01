import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function GET() {
  const allowSeed = process.env.NEXT_PUBLIC_DEV_ALLOW_ENV_SEED === '1';
  const isProd = process.env.NODE_ENV === 'production';

  if (!allowSeed || isProd) {
    return NextResponse.json({ error: 'Not enabled' }, { status: 404 });
  }

  return NextResponse.json({
    openai_api_key: process.env.OPENAI_API_KEY || '',
    wandb_api_key: process.env.WANDB_API_KEY || '',
    wandb_project: process.env.WANDB_PROJECT || 'weavehacks-rvla',
    wandb_entity: process.env.WANDB_ENTITY || '',
    redis_url: process.env.REDIS_URL || '',
    browserbase_api_key: process.env.BROWSERBASE_API_KEY || '',
    browserbase_project_id: process.env.BROWSERBASE_PROJECT_ID || '',
  });
}
