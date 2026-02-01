# W&B/Weave MCP Tools for Cursor

## Overview

The MCP server now includes **5 W&B/Weave tools** that let you interact with Weave traces, charts, and data directly from Cursor!

## Available Tools

### 1. `weave_get_traces`
Get recent Weave traces/runs.

**Parameters:**
- `limit` (optional, default: 20) - Maximum number of traces to return
- `op_name_filter` (optional) - Filter traces by operation name

**Example:**
```json
{
  "name": "weave_get_traces",
  "arguments": {
    "limit": 50,
    "op_name_filter": "record_openclaw_run"
  }
}
```

### 2. `weave_get_dashboard_url`
Get the Weave dashboard URL to view charts and visualizations in browser.

**Parameters:** None

**Returns:** Dashboard URL, entity, and project info

### 3. `weave_analyze_trace`
Analyze a specific Weave trace by ID. Get detailed information about inputs, outputs, and execution.

**Parameters:**
- `trace_id` (required) - The trace/run ID to analyze

**Example:**
```json
{
  "name": "weave_analyze_trace",
  "arguments": {
    "trace_id": "019c1b2e-92ea-75c0-9fc8-b69127139de6"
  }
}
```

### 4. `weave_query_traces`
Query Weave traces with filters. Find traces by operation name, date range, or other criteria.

**Parameters:**
- `op_name` (optional) - Filter by operation name
- `limit` (optional, default: 50) - Maximum number of results

**Example:**
```json
{
  "name": "weave_query_traces",
  "arguments": {
    "op_name": "plan_next_action",
    "limit": 100
  }
}
```

### 5. `weave_get_metrics`
Get performance metrics from Weave traces. Analyze execution times, success rates, and trends.

**Parameters:**
- `op_name` (optional) - Operation name to analyze
- `limit` (optional, default: 100) - Number of recent runs to analyze

**Returns:**
- Total runs, success/failure counts
- Average duration
- Success rate
- Per-operation metrics

## How to Use in Cursor

1. **Make sure MCP server is configured** (see `CURSOR_MCP_SETUP.md`)

2. **Restart Cursor** after adding tools

3. **Use the tools** - They'll appear in Cursor's MCP tools panel

4. **Example queries:**
   - "Get the last 20 Weave traces"
   - "Show me the Weave dashboard URL"
   - "Analyze trace ID 019c1b2e-92ea-75c0-9fc8-b69127139de6"
   - "Query all traces for 'record_openclaw_run'"
   - "Get performance metrics for all operations"

## What You Can Do

✅ **View all traces** - See every operation logged to Weave  
✅ **Get dashboard URL** - Open Weave UI in browser for charts  
✅ **Analyze specific traces** - Deep dive into any trace  
✅ **Query by operation** - Find traces by name  
✅ **Get metrics** - Performance analysis, success rates, durations  
✅ **All from Cursor** - No need to switch to browser!

## Example Outputs

### `weave_get_traces` returns:
```json
{
  "traces": [
    {
      "id": "019c1b2e-92ea-75c0-9fc8-b69127139de6",
      "op_name": "record_openclaw_run",
      "started_at": "2026-02-01T14:24:58",
      "duration": 45.2,
      "status": "success"
    }
  ],
  "count": 1,
  "limit": 20
}
```

### `weave_get_metrics` returns:
```json
{
  "total_runs": 50,
  "success_count": 45,
  "failed_count": 5,
  "avg_duration": 12.5,
  "success_rate": 0.9,
  "operations": {
    "record_openclaw_run": {
      "count": 10,
      "avg_duration": 15.2,
      "success_rate": 0.8
    }
  }
}
```

## Setup

The tools are already added to `src/rvla/mcp_stdio_server.py`. Just:

1. Make sure your Cursor MCP config includes the server (see `CURSOR_MCP_CONFIG.json`)
2. Restart Cursor
3. Start using the tools!

All tools use your existing Weave configuration (from environment variables).
