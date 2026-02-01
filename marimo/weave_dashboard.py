import os
from typing import Any

import marimo as mo
import weave

app = mo.App()


@app.cell
def _() -> tuple[str, str | None, int]:
    project = os.getenv("WANDB_PROJECT", "weavehacks-rvla")
    entity = os.getenv("WANDB_ENTITY")
    limit = int(os.getenv("WEAVE_CALL_LIMIT", "50"))
    return project, entity, limit


@app.cell
def _(project: str, entity: str | None) -> str:
    try:
        if entity:
            weave.init(f"{entity}/{project}")
        else:
            weave.init(project)
        status = f"Initialized Weave: {entity + '/' if entity else ''}{project}"
    except Exception as exc:
        status = f"Failed to initialize Weave: {exc}"
    return status


@app.cell
def _(status: str) -> None:
    mo.md(
        f"""
        # Weave Live Dashboard (Marimo)

        {status}

        This notebook reads the latest Weave calls and renders a quick preview.
        """
    )


@app.cell
def _() -> Any:
    calls = weave.get_calls()
    return calls


@app.cell
def _(calls: Any, limit: int) -> Any:
    if hasattr(calls, "head"):
        return calls.head(limit)
    try:
        return list(calls)[:limit]
    except Exception as exc:
        return {"error": f"Unable to preview calls: {exc}"}


if __name__ == "__main__":
    app.run()
