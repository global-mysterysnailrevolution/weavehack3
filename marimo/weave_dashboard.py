import os
from typing import Any
from datetime import datetime

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
def _(mo, status):
    mo.md(f"""
    # 🦞 Lobster Pot - Self-Improving Agent Dashboard

    {status}

    **WeaveHacks 3 Demo** - This dashboard visualizes how the Lobster Pot safety layer enables iterative self-improvement.

    The agent learns from Weave traces, identifies issues, generates suggestions, and improves with each iteration.
    Watch the metrics below to see improvement in real-time!
    """)
    return


@app.cell
def _(weave, limit):
    """Get recent calls for analysis."""
    try:
        calls = weave.get_op_runs(limit=limit)
        if hasattr(calls, "head"):
            recent_calls = calls.head(limit)
        else:
            recent_calls = list(calls)[:limit] if hasattr(calls, "__iter__") else []
        return (recent_calls,)
    except Exception as exc:
        return ({"error": f"Unable to get calls: {exc}"},)


@app.cell
def _(recent_calls, pd):
    """Convert calls to DataFrame for analysis."""
    try:
        if isinstance(recent_calls, dict) and "error" in recent_calls:
            return (recent_calls,)
        
        if hasattr(recent_calls, "to_pandas"):
            df = recent_calls.to_pandas()
        else:
            # Try to convert manually
            data = []
            for _df_call in recent_calls:
                try:
                    data.append({
                        "op_name": getattr(_df_call, "op_name", "unknown"),
                        "timestamp": getattr(_df_call, "started_at", None),
                        "duration": getattr(_df_call, "duration", None),
                        "status": getattr(_df_call, "status", "unknown"),
                    })
                except:
                    pass
            df = pd.DataFrame(data) if data else pd.DataFrame()
        return (df,)
    except Exception as exc:
        return ({"error": f"Unable to convert to DataFrame: {exc}"},)


@app.cell
def _(datetime, df, mo):
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
    return


@app.cell
def _(df, mo, pd):
    """Show agent performance trends."""
    if isinstance(df, dict) and "error" in df:
        pass
    else:
        try:
            if isinstance(df, pd.DataFrame) and "timestamp" in df.columns and "duration" in df.columns:
                _perf_agent_df = df[df["op_name"].astype(str).str.contains("agent|run|execute", case=False, na=False)]
                if len(_perf_agent_df) > 0:
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
    return


@app.cell
def _(mo, pd, recent_calls):
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
    return


@app.cell
def _(mo, recent_calls):
    """Show improvement suggestions based on Weave traces."""
    try:
        # Analyze calls for patterns
        total = len(list(recent_calls)) if not hasattr(recent_calls, "__len__") else len(recent_calls)

        # Look for iterative improvement patterns
        iteration_calls = []
        for call in recent_calls:
            op_name = str(getattr(call, "op_name", ""))
            if "run_pricing_iteration" in op_name.lower() or "iteration" in op_name.lower():
                try:
                    if hasattr(call, "output"):
                        output = call.output
                    elif hasattr(call, "result"):
                        output = call.result
                    else:
                        continue

                    if isinstance(output, dict) and "iteration" in output:
                        iteration_calls.append({
                            "iteration": output.get("iteration", 0),
                            "success": output.get("success", False),
                            "steps": output.get("steps", 0),
                            "events": output.get("events", 0),
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
            import pandas as pd
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
    return (pd,)




@app.cell
def _(recent_calls, weave):
    """Extract OpenClaw run details with full analysis."""
    openclaw_details = []
    try:
        items = list(recent_calls) if not hasattr(recent_calls, "__iter__") else recent_calls
        for _oc_call in items:
            _oc_op_name = str(getattr(_oc_call, "op_name", ""))
            if "record_openclaw_run" in _oc_op_name.lower():
                try:
                    # Try multiple ways to access the output
                    _oc_output = None
                    if hasattr(_oc_call, "output"):
                        _oc_output = _oc_call.output
                    elif hasattr(_oc_call, "result"):
                        _oc_output = _oc_call.result
                    elif hasattr(_oc_call, "return_value"):
                        _oc_output = _oc_call.return_value
                    elif hasattr(_oc_call, "get_output"):
                        _oc_output = _oc_call.get_output()
                    else:
                        # Try accessing as dict/object
                        try:
                            if isinstance(_oc_call, dict):
                                _oc_output = _oc_call.get("output") or _oc_call.get("result")
                            else:
                                # Try to get the call ID and fetch full call
                                _oc_call_id = getattr(_oc_call, "id", None) or getattr(_oc_call, "_id", None)
                                if _oc_call_id:
                                    try:
                                        _oc_full_call = weave.get_call(_oc_call_id)
                                        if _oc_full_call:
                                            _oc_output = getattr(_oc_full_call, "output", None) or getattr(_oc_full_call, "result", None)
                                    except:
                                        pass
                        except:
                            pass

                    if _oc_output is None:
                        # If we can't get output, still record basic info
                        openclaw_details.append({
                            "mode": "unknown",
                            "goal": "Unable to extract",
                            "iteration": 0,
                            "exit_code": None,
                            "analysis": {},
                            "timestamp": getattr(_oc_call, "started_at", None),
                            "raw_call": str(_oc_call)[:200],
                        })
                        continue

                    if isinstance(_oc_output, dict):
                        openclaw_details.append({
                            "mode": _oc_output.get("mode", "unknown"),
                            "goal": _oc_output.get("goal", "")[:100],  # Truncate long goals
                            "iteration": _oc_output.get("iteration", 0),
                            "exit_code": _oc_output.get("exit_code"),
                            "analysis": _oc_output.get("analysis", {}),
                            "timestamp": getattr(_oc_call, "started_at", None),
                        })
                except Exception as e:
                    # Still record that we found a call, even if we can't extract details
                    openclaw_details.append({
                        "mode": "error",
                        "goal": f"Error extracting: {str(e)[:50]}",
                        "iteration": 0,
                        "exit_code": None,
                        "analysis": {},
                        "timestamp": getattr(_oc_call, "started_at", None),
                    })
    except Exception as e:
        pass

    # Sort by iteration and timestamp (most recent first)
    openclaw_details.sort(key=lambda x: (x.get("iteration", 0), x.get("timestamp") or ""), reverse=True)
    return (openclaw_details,)


@app.cell
def _(openclaw_details, mo, pd):
    """Display OpenClaw runs with scores and analysis."""
    if not openclaw_details:
        mo.md("**No OpenClaw runs found yet.** Use the Beach panel to run OpenClaw tasks.")
    else:
        mo.md("## 🦀 OpenClaw Runs & Analysis")

        # Group by goal to show iteration progression
        _display_goals_map = {}
        for _display_detail in openclaw_details:
            _display_goal_key = _display_detail.get("goal", "unknown")[:50]
            if _display_goal_key not in _display_goals_map:
                _display_goals_map[_display_goal_key] = []
            _display_goals_map[_display_goal_key].append(_display_detail)

        for _display_goal_key, _display_runs in list(_display_goals_map.items())[:5]:  # Show top 5 goals
            mo.md(f"### Goal: `{_display_goal_key}...`")

            _display_runs_data = []
            for _display_run in _display_runs:
                _display_analysis = _display_run.get("analysis", {})
                _display_score = _display_analysis.get("score", "N/A")
                _display_suggestions = _display_analysis.get("suggestions", [])

                _display_runs_data.append({
                    "Iteration": _display_run.get("iteration", 0),
                    "Mode": _display_run.get("mode", "unknown"),
                    "Score": f"{_display_score:.2f}" if isinstance(_display_score, (int, float)) else str(_display_score),
                    "Exit": _display_run.get("exit_code", "N/A"),
                    "Suggestions": len(_display_suggestions),
                })

            if _display_runs_data:
                _display_runs_df = pd.DataFrame(_display_runs_data)
                mo.table(_display_runs_df)

                # Show suggestions from the latest run
                _display_latest = _display_runs[0]
                _display_latest_analysis = _display_latest.get("analysis", {})
                _display_latest_suggestions = _display_latest_analysis.get("suggestions", [])
                if _display_latest_suggestions:
                    mo.md("**Latest Prompt Suggestions:**")
                    for _display_sug in _display_latest_suggestions[:5]:
                        mo.md(f"- {_display_sug}")

            mo.md("---")
    return


@app.cell
def _(openclaw_details, mo):
    """Show prompt evolution across iterations."""
    if openclaw_details:
        # Group by goal and show how prompts improve
        _evol_goals_map = {}
        for _evol_detail in openclaw_details:
            _evol_goal_key = _evol_detail.get("goal", "unknown")[:50]
            if _evol_goal_key not in _evol_goals_map:
                _evol_goals_map[_evol_goal_key] = []
            _evol_goals_map[_evol_goal_key].append(_evol_detail)

        for _evol_goal_key, _evol_runs in list(_evol_goals_map.items())[:3]:  # Show top 3 goals
            if len(_evol_runs) < 2:
                continue  # Need at least 2 iterations to show evolution

            # Sort by iteration
            _evol_runs.sort(key=lambda x: x.get("iteration", 0))

            mo.md(f"### 📈 Prompt Evolution: `{_evol_goal_key}...`")

            for _evol_i, _evol_run in enumerate(_evol_runs):
                _evol_iteration = _evol_run.get("iteration", 0)
                _evol_analysis = _evol_run.get("analysis", {})
                _evol_score = _evol_analysis.get("score", "N/A")
                _evol_suggestions = _evol_analysis.get("suggestions", [])

                mo.md(f"**Iteration {_evol_iteration}** (Score: {_evol_score:.2f if isinstance(_evol_score, (int, float)) else _evol_score})")

                if _evol_suggestions:
                    mo.md("**Applied Suggestions:**")
                    for _evol_sug in _evol_suggestions[:3]:
                        mo.md(f"  ✓ {_evol_sug}")

                if _evol_i < len(_evol_runs) - 1:
                    mo.md("↓ *Next iteration incorporates feedback* ↓")

            mo.md("---")
    return


if __name__ == "__main__":
    app.run()
