# LobsterPot Guard Proxy (OpenClaw Layer)

LobsterPot is an OpenAI-compatible guard proxy you run in front of OpenClaw.  
OpenClaw points its provider `baseUrl` at LobsterPot, and LobsterPot forwards to the real LLM after applying safety checks and logging to Weave.

## Run locally

```bash
export LOBSTERPOT_UPSTREAM_BASE_URL=https://api.openai.com
export LOBSTERPOT_UPSTREAM_API_KEY=YOUR_OPENAI_KEY
export WANDB_API_KEY=...
export WANDB_PROJECT=weavehacks-rvla
export WANDB_ENTITY=your_entity   # optional

python scripts/start_lobsterpot_proxy.py
```

Default port: `8070` (override with `LOBSTERPOT_PORT`).

## OpenClaw provider config

Set OpenClaw to use LobsterPot as the provider base URL:

```
baseUrl: http://localhost:8070
model: lobsterpot/gpt-4o-mini
```

LobsterPot exposes:
- `POST /v1/chat/completions`
- `GET /v1/models`

## What it does

- Injects a safety system preamble
- Detects prompt-injection/exfil patterns
- Blocks high-risk requests
- Logs decisions to Weave

## Notes

- If you want to stream responses, we can add SSE/stream pass-through next.
- You can tune patterns with `SUSPICIOUS_PATTERNS` in `src/lobsterpot/proxy_server.py`.
