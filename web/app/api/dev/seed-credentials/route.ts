import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function GET() {
  // Always allow seeding from environment variables
  // This allows the app to use server-side environment variables
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
