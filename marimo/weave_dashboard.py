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
def _(recent_calls: Any) -> Any:
    """Extract OpenClaw run details with full analysis."""
    openclaw_details = []
    try:
        items = list(recent_calls) if not hasattr(recent_calls, "__iter__") else recent_calls
        for call in items:
            op_name = str(getattr(call, "op_name", ""))
            if "record_openclaw_run" in op_name.lower():
                try:
                    # Try multiple ways to access the output
                    output = None
                    if hasattr(call, "output"):
                        output = call.output
                    elif hasattr(call, "result"):
                        output = call.result
                    elif hasattr(call, "return_value"):
                        output = call.return_value
                    elif hasattr(call, "get_output"):
                        output = call.get_output()
                    else:
                        # Try accessing as dict/object
                        try:
                            if isinstance(call, dict):
                                output = call.get("output") or call.get("result")
                            else:
                                # Try to get the call ID and fetch full call
                                call_id = getattr(call, "id", None) or getattr(call, "_id", None)
                                if call_id:
                                    try:
                                        full_call = weave.get_call(call_id)
                                        if full_call:
                                            output = getattr(full_call, "output", None) or getattr(full_call, "result", None)
                                    except:
                                        pass
                        except:
                            pass
                    
                    if output is None:
                        # If we can't get output, still record basic info
                        openclaw_details.append({
                            "mode": "unknown",
                            "goal": "Unable to extract",
                            "iteration": 0,
                            "exit_code": None,
                            "analysis": {},
                            "timestamp": getattr(call, "started_at", None),
                            "raw_call": str(call)[:200],
                        })
                        continue
                    
                    if isinstance(output, dict):
                        openclaw_details.append({
                            "mode": output.get("mode", "unknown"),
                            "goal": output.get("goal", "")[:100],  # Truncate long goals
                            "iteration": output.get("iteration", 0),
                            "exit_code": output.get("exit_code"),
                            "analysis": output.get("analysis", {}),
                            "timestamp": getattr(call, "started_at", None),
                        })
                except Exception as e:
                    # Still record that we found a call, even if we can't extract details
                    openclaw_details.append({
                        "mode": "error",
                        "goal": f"Error extracting: {str(e)[:50]}",
                        "iteration": 0,
                        "exit_code": None,
                        "analysis": {},
                        "timestamp": getattr(call, "started_at", None),
                    })
    except Exception as e:
        pass
    
    # Sort by iteration and timestamp (most recent first)
    openclaw_details.sort(key=lambda x: (x.get("iteration", 0), x.get("timestamp") or ""), reverse=True)
    return openclaw_details


@app.cell
def _(openclaw_details: Any) -> None:
    """Display OpenClaw runs with scores and analysis."""
    if not openclaw_details:
        mo.md("**No OpenClaw runs found yet.** Use the Beach panel to run OpenClaw tasks.")
        return
    
    mo.md("## 🦀 OpenClaw Runs & Analysis")
    
    # Group by goal to show iteration progression
    goals_map = {}
    for detail in openclaw_details:
        goal_key = detail.get("goal", "unknown")[:50]
        if goal_key not in goals_map:
            goals_map[goal_key] = []
        goals_map[goal_key].append(detail)
    
    for goal_key, runs in list(goals_map.items())[:5]:  # Show top 5 goals
        mo.md(f"### Goal: `{goal_key}...`")
        
        runs_data = []
        for run in runs:
            analysis = run.get("analysis", {})
            score = analysis.get("score", "N/A")
            suggestions = analysis.get("suggestions", [])
            
            runs_data.append({
                "Iteration": run.get("iteration", 0),
                "Mode": run.get("mode", "unknown"),
                "Score": f"{score:.2f}" if isinstance(score, (int, float)) else str(score),
                "Exit": run.get("exit_code", "N/A"),
                "Suggestions": len(suggestions),
            })
        
        if runs_data:
            runs_df = pd.DataFrame(runs_data)
            mo.table(runs_df)
            
            # Show suggestions from the latest run
            latest = runs[0]
            latest_analysis = latest.get("analysis", {})
            latest_suggestions = latest_analysis.get("suggestions", [])
            if latest_suggestions:
                mo.md("**Latest Prompt Suggestions:**")
                for sug in latest_suggestions[:5]:
                    mo.md(f"- {sug}")
        
        mo.md("---")


@app.cell
def _(openclaw_details: Any) -> None:
    """Show prompt evolution across iterations."""
    if not openclaw_details:
        return
    
    # Group by goal and show how prompts improve
    goals_map = {}
    for detail in openclaw_details:
        goal_key = detail.get("goal", "unknown")[:50]
        if goal_key not in goals_map:
            goals_map[goal_key] = []
        goals_map[goal_key].append(detail)
    
    for goal_key, runs in list(goals_map.items())[:3]:  # Show top 3 goals
        if len(runs) < 2:
            continue  # Need at least 2 iterations to show evolution
        
        # Sort by iteration
        runs.sort(key=lambda x: x.get("iteration", 0))
        
        mo.md(f"### 📈 Prompt Evolution: `{goal_key}...`")
        
        for i, run in enumerate(runs):
            iteration = run.get("iteration", 0)
            analysis = run.get("analysis", {})
            score = analysis.get("score", "N/A")
            suggestions = analysis.get("suggestions", [])
            
            mo.md(f"**Iteration {iteration}** (Score: {score:.2f if isinstance(score, (int, float)) else score})")
            
            if suggestions:
                mo.md("**Applied Suggestions:**")
                for sug in suggestions[:3]:
                    mo.md(f"  ✓ {sug}")
            
            if i < len(runs) - 1:
                mo.md("↓ *Next iteration incorporates feedback* ↓")
        
        mo.md("---")


if __name__ == "__main__":
    app.run()
