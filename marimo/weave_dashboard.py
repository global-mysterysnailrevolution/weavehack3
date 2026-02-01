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
def _(mo, status: str) -> None:
    mo.md(f"""
    # 🦞 Lobster Pot - Self-Improving Agent Dashboard

    {status}

    **WeaveHacks 3 Demo** - This dashboard visualizes how the Lobster Pot safety layer enables iterative self-improvement.

    The agent learns from Weave traces, identifies issues, generates suggestions, and improves with each iteration.
    Watch the metrics below to see improvement in real-time!
    """)


@app.cell
def _(weave, limit: int) -> Any:
    """Get recent calls for analysis."""
    try:
        calls = weave.get_op_runs(limit=limit)
        if hasattr(calls, "head"):
            recent_calls = calls.head(limit)
        else:
            recent_calls = list(calls)[:limit] if hasattr(calls, "__iter__") else []
        return recent_calls
    except Exception as exc:
        return {"error": f"Unable to get calls: {exc}"}


@app.cell
def _(recent_calls: Any, pd) -> Any:
    """Convert calls to DataFrame for analysis."""
    try:
        if isinstance(recent_calls, dict) and "error" in recent_calls:
            return recent_calls
        
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
            df = pd.DataFrame(data) if data else pd.DataFrame()
        return df
    except Exception as exc:
        return {"error": f"Unable to convert to DataFrame: {exc}"}


@app.cell
def _(df: Any, datetime, mo) -> None:
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
def _(df: Any, mo) -> None:
    """Show agent performance trends."""
    if isinstance(df, dict) and "error" in df:
        return

    try:
        if isinstance(df, pd.DataFrame) and "timestamp" in df.columns and "duration" in df.columns:
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
def _(recent_calls: Any, pd, mo) -> None:
    """Display recent agent runs."""
    try:
        if isinstance(recent_calls, dict):
            mo.md("**Error loading calls.**")
            return
            
        agent_runs = []
        for _call in recent_calls:
            _op_name = str(getattr(_call, "op_name", ""))
            if any(keyword in _op_name.lower() for keyword in ["agent", "run", "execute", "goal"]):
                agent_runs.append({
                    "Operation": _op_name,
                    "Status": getattr(_call, "status", "unknown"),
                    "Duration": f"{getattr(_call, 'duration', 0):.2f}s" if hasattr(_call, "duration") else "N/A",
                })

        if agent_runs:
            runs_df = pd.DataFrame(agent_runs)
            mo.table(runs_df.head(10))
        else:
            mo.md("**No recent agent runs found.**")
    except Exception as exc:
        mo.md(f"**Error displaying runs:** {exc}")


@app.cell
def _(recent_calls: Any, mo, pd) -> None:
    """Show improvement suggestions based on Weave traces."""
    try:
        if isinstance(recent_calls, dict):
            mo.md("**Error loading calls.**")
            return
            
        # Analyze calls for patterns
        total = len(list(recent_calls)) if not hasattr(recent_calls, "__len__") else len(recent_calls)

        # Look for iterative improvement patterns
        iteration_calls = []
        for _call_item in recent_calls:
            _op_name_item = str(getattr(_call_item, "op_name", ""))
            if "run_pricing_iteration" in _op_name_item.lower() or "iteration" in _op_name_item.lower():
                try:
                    if hasattr(_call_item, "output"):
                        _output = _call_item.output
                    elif hasattr(_call_item, "result"):
                        _output = _call_item.result
                    else:
                        continue

                    if isinstance(_output, dict) and "iteration" in _output:
                        iteration_calls.append({
                            "iteration": _output.get("iteration", 0),
                            "success": _output.get("success", False),
                            "steps": _output.get("steps", 0),
                            "events": _output.get("events", 0),
                        })
                except:
                    pass

        if iteration_calls:
            # Sort by iteration
            iteration_calls.sort(key=lambda x: x.get("iteration", 0))

            mo.md(
                f"""
                ## 📈 Iterative Improvement Tracking
                Found {len(iteration_calls)} iterations of pricing task:
                """
            )

            # Show improvement trend
            if len(iteration_calls) > 1:
                first = iteration_calls[0]
                last = iteration_calls[-1]

                improvements = []
                if last["steps"] > first["steps"]:
                    improvements.append(f"✅ More steps ({first['steps']} → {last['steps']}) - more thorough")
                if last["success"] and not first["success"]:
                    improvements.append("✅ Success improved (failed → succeeded)")
                if last["events"] > first["events"]:
                    improvements.append(f"✅ More events ({first['events']} → {last['events']}) - better logging")

                if improvements:
                    mo.md("**Improvements detected:**")
                    for imp in improvements:
                        mo.md(f"- {imp}")
                else:
                    mo.md("**No clear improvement yet** - may need more iterations")

            # Show iteration table
            iter_df = pd.DataFrame(iteration_calls)
            mo.table(iter_df)
        elif total > 0:
            mo.md(
                f"""
                ## 💡 Improvement Suggestions

                Based on {total} Weave traces:

                1. **Monitor execution patterns** - Review action sequences for optimization opportunities
                2. **Track success rates** - Identify which goals and actions lead to better outcomes  
                3. **Analyze context usage** - Optimize RLM context examination for efficiency
                4. **Compare runs** - Use iterative runs to improve agent performance

                *Run `scripts/showcase_weave_improvement.py` to see iterative improvement in action.*
                """
            )
        else:
            mo.md("**Run your agent to get improvement suggestions.**")
    except Exception as exc:
        mo.md(f"**Note:** {exc}")


@app.cell
def _(recent_calls: Any, weave) -> list[dict]:
    """Extract OpenClaw run details with full analysis."""
    openclaw_details = []
    try:
        if isinstance(recent_calls, dict):
            return []
            
        items = list(recent_calls) if not hasattr(recent_calls, "__iter__") else recent_calls
        for _call_detail in items:
            _op_name_detail = str(getattr(_call_detail, "op_name", ""))
            if "record_openclaw_run" in _op_name_detail.lower():
                try:
                    # Try multiple ways to access the output
                    _output_detail = None
                    if hasattr(_call_detail, "output"):
                        _output_detail = _call_detail.output
                    elif hasattr(_call_detail, "result"):
                        _output_detail = _call_detail.result
                    elif hasattr(_call_detail, "return_value"):
                        _output_detail = _call_detail.return_value
                    elif hasattr(_call_detail, "get_output"):
                        _output_detail = _call_detail.get_output()
                    else:
                        # Try accessing as dict/object
                        try:
                            if isinstance(_call_detail, dict):
                                _output_detail = _call_detail.get("output") or _call_detail.get("result")
                            else:
                                # Try to get the call ID and fetch full call
                                _call_id = getattr(_call_detail, "id", None) or getattr(_call_detail, "_id", None)
                                if _call_id:
                                    try:
                                        _full_call = weave.get_op_run(_call_id)
                                        if _full_call:
                                            _output_detail = getattr(_full_call, "output", None) or getattr(_full_call, "result", None)
                                    except:
                                        pass
                        except:
                            pass

                    if _output_detail is None:
                        # If we can't get output, still record basic info
                        openclaw_details.append({
                            "mode": "unknown",
                            "goal": "Unable to extract",
                            "iteration": 0,
                            "exit_code": None,
                            "analysis": {},
                            "timestamp": getattr(_call_detail, "started_at", None),
                            "raw_call": str(_call_detail)[:200],
                        })
                        continue

                    if isinstance(_output_detail, dict):
                        openclaw_details.append({
                            "mode": _output_detail.get("mode", "unknown"),
                            "goal": _output_detail.get("goal", "")[:100],  # Truncate long goals
                            "iteration": _output_detail.get("iteration", 0),
                            "exit_code": _output_detail.get("exit_code"),
                            "analysis": _output_detail.get("analysis", {}),
                            "timestamp": getattr(_call_detail, "started_at", None),
                        })
                except Exception as e:
                    # Still record that we found a call, even if we can't extract details
                    openclaw_details.append({
                        "mode": "error",
                        "goal": f"Error extracting: {str(e)[:50]}",
                        "iteration": 0,
                        "exit_code": None,
                        "analysis": {},
                        "timestamp": getattr(_call_detail, "started_at", None),
                    })
    except Exception as e:
        pass

    # Sort by iteration and timestamp (most recent first)
    openclaw_details.sort(key=lambda x: (x.get("iteration", 0), x.get("timestamp") or ""), reverse=True)
    return openclaw_details


@app.cell
def _(openclaw_details: list[dict], mo, pd) -> None:
    """Display OpenClaw runs with scores and analysis."""
    if not openclaw_details:
        mo.md("**No OpenClaw runs found yet.** Use the Beach panel to run OpenClaw tasks.")
        return

    mo.md("## 🦀 OpenClaw Runs & Analysis")

    # Group by goal to show iteration progression
    goals_map = {}
    for _detail in openclaw_details:
        _goal_key = _detail.get("goal", "unknown")[:50]
        if _goal_key not in goals_map:
            goals_map[_goal_key] = []
        goals_map[_goal_key].append(_detail)

    for _goal_key, _runs in list(goals_map.items())[:5]:  # Show top 5 goals
        mo.md(f"### Goal: `{_goal_key}...`")

        _runs_data = []
        for _run in _runs:
            _analysis = _run.get("analysis", {})
            _score = _analysis.get("score", "N/A")
            _suggestions = _analysis.get("suggestions", [])

            _runs_data.append({
                "Iteration": _run.get("iteration", 0),
                "Mode": _run.get("mode", "unknown"),
                "Score": f"{_score:.2f}" if isinstance(_score, (int, float)) else str(_score),
                "Exit": _run.get("exit_code", "N/A"),
                "Suggestions": len(_suggestions),
            })

        if _runs_data:
            _runs_df = pd.DataFrame(_runs_data)
            mo.table(_runs_df)

            # Show suggestions from the latest run
            _latest = _runs[0]
            _latest_analysis = _latest.get("analysis", {})
            _latest_suggestions = _latest_analysis.get("suggestions", [])
            if _latest_suggestions:
                mo.md("**Latest Prompt Suggestions:**")
                for _sug in _latest_suggestions[:5]:
                    mo.md(f"- {_sug}")

        mo.md("---")


@app.cell
def _(openclaw_details: list[dict], mo) -> None:
    """Show prompt evolution across iterations."""
    if not openclaw_details:
        return

    # Group by goal and show how prompts improve
    _goals_map_evolution = {}
    for _detail_evolution in openclaw_details:
        _goal_key_evolution = _detail_evolution.get("goal", "unknown")[:50]
        if _goal_key_evolution not in _goals_map_evolution:
            _goals_map_evolution[_goal_key_evolution] = []
        _goals_map_evolution[_goal_key_evolution].append(_detail_evolution)

    for _goal_key_evolution, _runs_evolution in list(_goals_map_evolution.items())[:3]:  # Show top 3 goals
        if len(_runs_evolution) < 2:
            continue  # Need at least 2 iterations to show evolution

        # Sort by iteration
        _runs_evolution.sort(key=lambda x: x.get("iteration", 0))

        mo.md(f"### 📈 Prompt Evolution: `{_goal_key_evolution}...`")

        for i, _run_evolution in enumerate(_runs_evolution):
            _iteration_evolution = _run_evolution.get("iteration", 0)
            _analysis_evolution = _run_evolution.get("analysis", {})
            _score_evolution = _analysis_evolution.get("score", "N/A")
            _suggestions_evolution = _analysis_evolution.get("suggestions", [])

            mo.md(f"**Iteration {_iteration_evolution}** (Score: {_score_evolution:.2f if isinstance(_score_evolution, (int, float)) else _score_evolution})")

            if _suggestions_evolution:
                mo.md("**Applied Suggestions:**")
                for _sug_evolution in _suggestions_evolution[:3]:
                    mo.md(f"  ✓ {_sug_evolution}")

            if i < len(_runs_evolution) - 1:
                mo.md("↓ *Next iteration incorporates feedback* ↓")

        mo.md("---")


if __name__ == "__main__":
    app.run()
