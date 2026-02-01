import { NextRequest } from 'next/server';

export const runtime = 'nodejs';

export async function GET(req: NextRequest) {
  return new Response(
    JSON.stringify({ 
      message: 'API routes are working!',
      timestamp: new Date().toISOString(),
    }),
    { 
      status: 200, 
      headers: { 'Content-Type': 'application/json' } 
    }
  );
}
