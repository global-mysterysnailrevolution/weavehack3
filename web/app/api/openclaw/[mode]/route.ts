import { NextRequest } from 'next/server';

export const runtime = 'nodejs';

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ mode: string }> | { mode: string } }
) {
  const resolvedParams = await Promise.resolve(params);
  return new Response(
    JSON.stringify({
      error: 'Method not allowed. Use POST to run OpenClaw commands.',
      hint: 'This endpoint requires POST requests with a JSON body containing { "goal": "...", "iteration": 0 }',
    }),
    {
      status: 405,
      headers: { 'Content-Type': 'application/json', 'Allow': 'POST' },
    }
  );
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ mode: string }> | { mode: string } }
) {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL;
  
  if (!apiBase) {
    return new Response(
      JSON.stringify({
        error: 'OpenClaw backend not configured. Set NEXT_PUBLIC_API_BASE_URL to your FastAPI server.',
      }),
      {
        status: 501,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }

  const resolvedParams = await Promise.resolve(params);
  const mode = resolvedParams.mode;
  if (mode !== 'beach' && mode !== 'sea') {
    return new Response(
      JSON.stringify({ error: 'Invalid mode. Use "beach" or "sea".' }),
      {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }

  try {
    const body = await req.json();
    const backendUrl = `${apiBase.replace(/\/$/, '')}/api/openclaw/${mode}`;

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return new Response(
        JSON.stringify({ error: `Backend error: ${errorText}` }),
        {
          status: response.status,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Stream the response
    return new Response(response.body, {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
      },
    });
  } catch (error: any) {
    return new Response(
      JSON.stringify({ error: `Proxy error: ${error.message}` }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}
