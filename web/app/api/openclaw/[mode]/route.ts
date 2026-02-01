import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function POST(_req: NextRequest) {
  return NextResponse.json(
    {
      error: 'OpenClaw backend not configured. Set NEXT_PUBLIC_API_BASE_URL to your FastAPI server.',
    },
    { status: 501 }
  );
}
