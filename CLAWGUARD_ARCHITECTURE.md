# ClawGuard Architecture

## Overview

ClawGuard is a safety sandbox layer for OpenClaw that:
1. **Sandboxes** OpenClaw actions before execution
2. **Analyzes** action trees for safety risks
3. **Modifies** prompts to add safety constraints
4. **Re-validates** in sandbox until safe
5. **Approves** or blocks execution
6. **Self-improves** using Weave traces and eval

## Core Components

### 1. Sandbox Runner (`src/clawguard/sandbox.py`)
- Spawns OpenClaw instances in "dry-run" mode
- Captures all planned actions via Weave traces
- Returns action tree without executing

### 2. Action Tree Analyzer (`src/clawguard/analyzer.py`)
- Detects prompt injection (untrusted content → instructions)
- Flags dangerous actions (shell, file delete, etc.)
- Detects cost anomalies
- Scores safety using Weave eval

### 3. Prompt Modifier (`src/clawguard/modifier.py`)
- Uses GPT-4o to review and modify prompts
- Adds safety constraints
- Implements closed-loop self-improvement:
  - Check → Fail → Modify → Re-check → Pass

### 4. Approval Gate (`src/clawguard/gate.py`)
- Visualizes "what would happen"
- Requires confirmation for risky actions
- Executes only after approval

### 5. Self-Improvement Engine (`src/clawguard/improvement.py`)
- Analyzes Weave traces of past runs
- Identifies patterns in failures
- Updates safety rules automatically
- Uses Weave eval to measure improvement

## Data Flow

```
User Request
    ↓
Sandbox Runner → OpenClaw (dry-run) → Weave Trace
    ↓
Action Tree Analyzer → Safety Checks → Risk Score
    ↓
[If Risk Detected]
    ↓
Prompt Modifier → Add Safety Constraints → Modified Prompt
    ↓
Sandbox Runner (again) → Re-check → New Risk Score
    ↓
[Loop until safe or max iterations]
    ↓
Approval Gate → Visualize → User Confirms
    ↓
Execute (if approved) → Real OpenClaw → Weave Trace
    ↓
Self-Improvement Engine → Analyze → Update Rules
```

## Weave Integration

- **Traces**: Every sandbox run and real execution
- **Eval**: Safety scoring, cost tracking, completion quality
- **Self-Improvement**: Analyze traces → update rules → measure improvement

## Web UI

- **Safety Dashboard**: Real-time view of sandbox runs
- **Action Tree Viewer**: Visualize what OpenClaw would do
- **Risk Indicators**: Color-coded safety scores
- **Approval Interface**: Review and confirm actions
- **Improvement Metrics**: Show how rules are getting better
