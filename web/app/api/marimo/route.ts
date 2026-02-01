import { NextRequest } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function getTargetBaseUrl(): URL | null {
  const raw = process.env.MARIMO_PROXY_URL;
  if (!raw) {
    return null;
  }
  try {
    return new URL(raw);
  } catch {
    return null;
  }
}

export async function GET(req: NextRequest) {
  const baseUrl = getTargetBaseUrl();
  
  if (!baseUrl) {
    return new Response(
      JSON.stringify({ 
        error: 'MARIMO_PROXY_URL is not configured. Set it in Vercel environment variables.',
        hint: 'Point it to your published Marimo notebook URL (e.g., https://marimo.app/l/...)'
      }),
      { 
        status: 503, 
        headers: { 'Content-Type': 'application/json' } 
      }
    );
  }

  try {
    // For root path, redirect to the base URL
    const targetUrl = new URL(baseUrl.toString());
    req.nextUrl.searchParams.forEach((value, key) => {
      targetUrl.searchParams.append(key, value);
    });

    const upstream = await fetch(targetUrl.toString(), {
      headers: {
        'User-Agent': req.headers.get('user-agent') || 'marimo-proxy',
      },
      redirect: 'follow',
    });

    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        'Content-Type': upstream.headers.get('content-type') || 'text/html; charset=utf-8',
        'Cache-Control': 'no-store',
      },
    });
  } catch (error: any) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
