import os
from typing import Any
from datetime import datetime, timedelta

import marimo as mo
import weave
import pandas as pd

app = mo.App()


@app.cell
def _() -> tuple[str, str | None, int]:
    project = os.getenv("WANDB_PROJECT", "weavehacks-rvla")
    entity = os.getenv("WANDB_ENTITY")
    limit = int(os.getenv("WEAVE_CALL_LIMIT", "100"))
    return project, entity, limit


@app.cell
def _(project: str, entity: str | None) -> str:
    try:
        if entity:
            weave.init(f"{entity}/{project}")
        else:
            weave.init(project)
        status = f"✅ Initialized Weave: {entity + '/' if entity else ''}{project}"
    except Exception as exc:
        status = f"❌ Failed to initialize Weave: {exc}"
    return status


@app.cell
def _(status: str) -> None:
    mo.md(
        f"""
        # 🦞 Agent Improvement Dashboard

        {status}

        This dashboard analyzes Weave traces to show how your RLM-VLA agent improves over time.
        It tracks performance metrics, action patterns, and identifies optimization opportunities.
        """
    )


@app.cell
def _() -> Any:
    calls = weave.get_calls()
    return calls


@app.cell
def _(calls: Any, limit: int) -> Any:
    """Get recent calls for analysis."""
    try:
        if hasattr(calls, "head"):
            recent_calls = calls.head(limit)
        else:
            recent_calls = list(calls)[:limit]
        return recent_calls
    except Exception as exc:
        return {"error": f"Unable to get calls: {exc}"}


@app.cell
def _(recent_calls: Any) -> Any:
    """Convert calls to DataFrame for analysis."""
    try:
        if hasattr(recent_calls, "to_pandas"):
            df = recent_calls.to_pandas()
        else:
            # Try to convert manually
            data = []
            for call in recent_calls:
                try:
                    data.append({
                        "op_name": getattr(call, "op_name", "unknown"),
                        "timestamp": getattr(call, "started_at", None),
                        "duration": getattr(call, "duration", None),
                        "status": getattr(call, "status", "unknown"),
                    })
                except:
                    pass
            df = pd.DataFrame(data)
        return df
    except Exception as exc:
        return {"error": f"Unable to convert to DataFrame: {exc}"}


@app.cell
def _(df: Any) -> None:
    """Display agent execution summary."""
    if isinstance(df, dict) and "error" in df:
        mo.md(f"**Error:** {df['error']}")
    elif df is not None and len(df) > 0:
        total_calls = len(df)
        agent_calls = df[df["op_name"].astype(str).str.contains("agent|run|execute", case=False, na=False)]
        agent_count = len(agent_calls) if len(agent_calls) > 0 else 0
        
        mo.md(
            f"""
            ## 📊 Execution Summary
            
            - **Total Weave Calls:** {total_calls}
            - **Agent Executions:** {agent_count}
            - **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
        )
    else:
        mo.md("**No calls found.** Start running your agent to see data here.")


@app.cell
def _(df: Any) -> None:
    """Show agent performance trends."""
    if isinstance(df, dict) and "error" in df:
        return
    
    try:
        if "timestamp" in df.columns and "duration" in df.columns:
            agent_df = df[df["op_name"].astype(str).str.contains("agent|run|execute", case=False, na=False)]
            if len(agent_df) > 0:
                mo.md(
                    """
                    ## 📈 Performance Trends
                    
                    *Performance metrics will appear here as you run more agent executions.*
                    
                    Track improvements in:
                    - Execution speed
                    - Success rates
                    - Action efficiency
                    - Context usage
                    """
                )
            else:
                mo.md("**No agent executions found yet.** Run your agent to see performance data.")
        else:
            mo.md("**Performance data:** Available after agent runs.")
    except Exception as exc:
        mo.md(f"**Note:** {exc}")


@app.cell
def _(recent_calls: Any) -> None:
    """Display recent agent runs."""
    try:
        agent_runs = []
        for call in recent_calls:
            op_name = str(getattr(call, "op_name", ""))
            if any(keyword in op_name.lower() for keyword in ["agent", "run", "execute", "goal"]):
                agent_runs.append({
                    "Operation": op_name,
                    "Status": getattr(call, "status", "unknown"),
                    "Duration": f"{getattr(call, 'duration', 0):.2f}s" if hasattr(call, "duration") else "N/A",
                })
        
        if agent_runs:
            runs_df = pd.DataFrame(agent_runs)
            mo.table(runs_df.head(10))
        else:
            mo.md("**No recent agent runs found.**")
    except Exception as exc:
        mo.md(f"**Error displaying runs:** {exc}")


@app.cell
def _(recent_calls: Any) -> None:
    """Show improvement suggestions based on Weave traces."""
    try:
        # Analyze calls for patterns
        total = len(list(recent_calls)) if not hasattr(recent_calls, "__len__") else len(recent_calls)
        
        if total > 0:
            mo.md(
                f"""
                ## 💡 Improvement Suggestions
                
                Based on {total} Weave traces:
                
                1. **Monitor execution patterns** - Review action sequences for optimization opportunities
                2. **Track success rates** - Identify which goals and actions lead to better outcomes  
                3. **Analyze context usage** - Optimize RLM context examination for efficiency
                4. **Compare runs** - Use "Cook Longer" to iterate and improve agent performance
                
                *Suggestions update automatically as you run more agent executions.*
                """
            )
        else:
            mo.md("**Run your agent to get improvement suggestions.**")
    except Exception as exc:
        mo.md(f"**Note:** {exc}")


@app.cell
def _(recent_calls: Any, limit: int) -> Any:
    """Extract OpenClaw runs if available."""
    try:
        if hasattr(recent_calls, "to_pandas"):
            df = recent_calls.to_pandas()
            mask = df["op_name"].astype(str).str.contains("record_openclaw_run|openclaw", case=False, na=False)
            openclaw_runs = df[mask].head(limit)
            return openclaw_runs if len(openclaw_runs) > 0 else None
    except:
        pass

    try:
        items = list(recent_calls) if not hasattr(recent_calls, "__iter__") else recent_calls
        filtered = [
            item for item in items 
            if "openclaw" in str(getattr(item, "op_name", "")).lower()
        ]
        return filtered[:limit] if filtered else None
    except:
        return None


@app.cell
def _(openclaw_runs: Any) -> None:
    """Display OpenClaw run data if available."""
    if openclaw_runs is not None and len(openclaw_runs) > 0:
        mo.md("## 🦀 OpenClaw Runs")
        if hasattr(openclaw_runs, "head"):
            mo.table(openclaw_runs.head(10))
        else:
            mo.md(f"Found {len(openclaw_runs)} OpenClaw runs.")


if __name__ == "__main__":
    app.run()
