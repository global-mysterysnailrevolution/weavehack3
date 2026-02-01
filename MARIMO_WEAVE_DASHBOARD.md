# Marimo + Weave Dashboard

This notebook renders recent Weave calls inside a Marimo app and is intended to be embedded in the web UI.

## Run locally

```bash
pip install marimo weave wandb
export WANDB_API_KEY=...
export WANDB_PROJECT=weavehacks-rvla
export WANDB_ENTITY=your_entity   # optional
export WEAVE_CALL_LIMIT=50        # optional

marimo run marimo/weave_dashboard.py
```

## Publish and embed

1) Publish the Marimo notebook (Marimo Cloud or your own host).
2) Set the Vercel env var:

```
MARIMO_PROXY_URL=https://marimo.app/l/<your-notebook-id>
```

3) Deploy. The UI will embed the dashboard via `/api/marimo`.
