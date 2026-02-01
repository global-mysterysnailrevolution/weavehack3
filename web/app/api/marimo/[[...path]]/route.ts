import { NextRequest } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function getTargetBaseUrl(): URL {
  const raw = process.env.MARIMO_PROXY_URL;
  if (!raw) {
    throw new Error('MARIMO_PROXY_URL is not set');
  }
  return new URL(raw);
}

export async function GET(req: NextRequest, { params }: { params: { path?: string[] } }) {
  try {
    const baseUrl = getTargetBaseUrl();
    const pathParts = params.path || [];
    const relativePath = pathParts.length ? pathParts.join('/') : '';

    const targetUrl = new URL(relativePath, baseUrl);
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
