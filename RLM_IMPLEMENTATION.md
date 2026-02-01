# RLM (Recursive Language Model) Implementation for VLA

## Overview

This implementation follows the [Recursive Language Models paper (arXiv:2512.24601)](https://arxiv.org/abs/2512.24601) to enable ultralong context processing for Vision-Language-Action (VLA) tasks.

## Key RLM Concepts Implemented

### 1. **Programmatic Context Examination**
Instead of loading entire context into the model, we examine it programmatically:
- Context is treated as **external environment**
- Agent queries context with specific questions
- Only relevant snippets are extracted and used

### 2. **Recursive Decomposition**
Agent recursively calls itself to decompose complex tasks:
- Tasks are broken into subtasks
- Each subtask can be further decomposed
- Creates a tree structure of task decomposition

### 3. **Snippet Processing**
Long context is processed in chunks:
- Context split into overlapping snippets
- Each snippet examined for relevance
- Most relevant snippets combined for planning

## Implementation Files

### `src/rvla/rlm_core.py`
Core RLM functionality:
- `examine_context_snippet()`: Examine a snippet programmatically
- `select_relevant_snippets()`: Find most relevant snippets from large context
- `process_context_recursively()`: Process long context in chunks
- `RLMContextExaminer`: Main class for context examination

### `src/rvla/rlm_decomposer.py`
Recursive decomposition engine:
- `decompose_task()`: Decompose task into subtasks
- `recursive_decompose()`: Recursively build decomposition tree
- `RLMDecomposer`: Main class for task decomposition

### `src/rvla/agent.py` (Updated)
Integrated RLM into agent:
- Uses `RLMContextExaminer` when context > 20 events
- Examines context programmatically before planning
- Combines RLM summary with recent events for planning

## How It Works

### Context Examination Flow:
```
1. Agent accumulates events (observations, actions, plans)
2. When events > 20, RLM kicks in:
   a. Split context into overlapping snippets (1000 chars, 200 overlap)
   b. Examine each snippet programmatically
   c. Select top 5 most relevant snippets
   d. Combine relevant snippets into summary
3. Use summary + recent events for planning
```

### Recursive Decomposition Flow:
```
1. Agent receives complex task
2. RLM decomposer analyzes task
3. If complex, breaks into 2-4 subtasks
4. Each subtask recursively decomposed
5. Creates tree of executable actions
```

## Benefits

1. **Ultralong Context**: Can handle contexts 2 orders of magnitude beyond model limits
2. **Efficiency**: Only examines relevant parts of context
3. **Scalability**: Works for 100+ step tasks without token bloat
4. **Intelligence**: Programmatic examination finds relevant information

## Usage Example

```python
from rvla.rlm_core import RLMContextExaminer
from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver

# RLM is automatically used when context gets long
workspace = workspace_from_env()
driver = WebDriver()
result = run_agent("extract pricing from multi-page site", driver, workspace)

# RLM will:
# 1. Examine long event history programmatically
# 2. Extract relevant information
# 3. Use it for planning without token bloat
```

## Integration with VLA

- **Vision**: GPT-4o analyzes screenshots
- **Language**: GPT-4o plans actions
- **Action**: Browserbase executes browser actions
- **RLM**: Examines long context programmatically
- **Weave**: Traces all operations
- **Redis**: Stores context externally

## Next Steps

1. ✅ RLM core implementation
2. ✅ Integration with agent
3. ⏳ Self-improvement loop (analyze Weave traces)
4. ⏳ Redis vector search for semantic retrieval
5. ⏳ Demo task implementation
