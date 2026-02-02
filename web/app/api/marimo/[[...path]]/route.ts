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

export async function GET(
  req: NextRequest,
  { params }: { params?: Promise<{ path?: string[] }> | { path?: string[] } }
) {
  const baseUrl = getTargetBaseUrl();
  
  if (!baseUrl) {
    // Return HTML page with instructions instead of JSON error
    const html = `
<!DOCTYPE html>
<html>
<head>
  <title>Marimo Dashboard - Configuration Required</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      padding: 2rem;
      max-width: 800px;
      margin: 0 auto;
    }
    .container {
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 2rem;
    }
    h1 { color: #60a5fa; margin-top: 0; }
    code {
      background: #0f172a;
      padding: 0.2rem 0.4rem;
      border-radius: 4px;
      font-family: 'Courier New', monospace;
    }
    .step {
      margin: 1.5rem 0;
      padding: 1rem;
      background: #0f172a;
      border-left: 3px solid #60a5fa;
    }
    .link {
      color: #60a5fa;
      text-decoration: none;
    }
    .link:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="container">
    <h1>📊 Marimo Dashboard Configuration</h1>
    <p>The Marimo dashboard requires configuration to visualize Weave traces.</p>
    
    <div class="step">
      <h3>Option 1: Use Published Marimo Notebook</h3>
      <p>1. Publish your Marimo notebook at <a href="https://marimo.app" class="link">marimo.app</a></p>
      <p>2. Set <code>MARIMO_PROXY_URL</code> in Vercel environment variables</p>
      <p>3. Point it to your notebook URL (e.g., <code>https://marimo.app/l/your-notebook-id</code>)</p>
    </div>
    
    <div class="step">
      <h3>Option 2: Run Marimo Locally</h3>
      <p>Run this command to start Marimo locally:</p>
      <pre style="background: #0f172a; padding: 1rem; border-radius: 4px; overflow-x: auto;"><code>marimo edit marimo/weave_dashboard.py</code></pre>
      <p>Then open the URL shown in your terminal.</p>
    </div>
    
    <div class="step">
      <h3>Option 3: View in W&B Dashboard</h3>
      <p>All traces are visible in the Weave dashboard:</p>
      <p><a href="https://wandb.ai/globalmysterysnailrevolution-provigen-ai/weavehacks-rvla/weave" class="link" target="_blank">Open Weave Dashboard</a></p>
    </div>
    
    <p style="margin-top: 2rem; color: #94a3b8; font-size: 0.9rem;">
      Once configured, refresh this page to see the Marimo dashboard.
    </p>
  </div>
</body>
</html>
    `;
    
    return new Response(html, {
      status: 200,
      headers: { 
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-store',
      }
    });
  }

  try {
    // Handle optional catch-all: params.path is undefined for /api/marimo, or array for /api/marimo/...
    const resolvedParams = params ? await Promise.resolve(params) : {};
    const pathParts = resolvedParams.path || [];
    const relativePath = pathParts.length ? pathParts.join('/') : '';

    // Build target URL: if no path parts, use base URL; otherwise append path
    const targetUrl = pathParts.length 
      ? new URL(relativePath, baseUrl)
      : new URL(baseUrl.toString());
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
