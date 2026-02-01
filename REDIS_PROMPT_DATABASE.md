# Redis Prompt Database

## Overview

The Redis Prompt Database is a learning system that:
1. **Extracts problem patterns** from Weave traces after OpenClaw runs
2. **Stores improved prompts** with structured metadata in Redis
3. **Retrieves relevant prompts** based on task context and similarity
4. **Makes learned prompts available as tools** for OpenClaw to use automatically

This enables **true self-improvement**: the system learns from past mistakes and successes, then applies that knowledge to future similar tasks.

## Architecture

### Components

1. **`PromptDatabase`** (`src/rvla/prompt_database.py`)
   - Redis-based storage for learned prompts
   - Falls back to in-memory storage if Redis unavailable
   - Indexes prompts by task type for fast retrieval

2. **`LearnedPrompt`** (dataclass)
   - Stores original prompt, improved prompt, problem patterns, metadata
   - Includes success rate, usage count, timestamps

3. **`ProblemPattern`** (dataclass)
   - Represents a problem identified from Weave traces
   - Includes error indicators, success indicators, frequency

4. **Integration** (`api/main.py`)
   - Automatically stores prompts after successful beach runs
   - Retrieves and injects relevant prompts before OpenClaw execution

## Data Flow

```
OpenClaw Run (Beach Mode)
    ↓
Weave Trace Captured
    ↓
Analysis Extracted (score, suggestions, patterns)
    ↓
Problem Patterns Identified
    ↓
Learned Prompt Created & Stored in Redis
    ↓
[Next Similar Task]
    ↓
Relevant Prompts Retrieved from Redis
    ↓
Prompt Tool Injected into OpenClaw Goal
    ↓
OpenClaw Uses Learned Strategy
```

## How It Works

### 1. Problem Pattern Extraction

When an OpenClaw run completes, the system:

- Analyzes the output for common problems:
  - `navigation_failure`: Errors during navigation
  - `missing_search`: No web searches performed
  - `incomplete_output`: Missing JSON/documentation
  - `missing_screenshots`: No screenshots captured
  - `pricing_extraction_failure`: Failed to extract prices

- Extracts patterns from Weave traces:
  - Event sequences
  - Error messages
  - Success indicators
  - Context keywords

### 2. Prompt Storage

After a successful improvement (score > 0.7, iteration > 0):

```python
learned_prompt = prompt_db.create_learned_prompt(
    original_prompt=original_goal,
    improved_prompt=goal_with_suggestions,
    analysis=analysis_results,
    goal=original_goal,
    task_type="pricing_extraction",
    trace_data=trace_data,
)
prompt_db.store_prompt(learned_prompt)
```

The prompt is stored with:
- **Task type** (e.g., "pricing_extraction", "web_navigation")
- **Problem patterns** it addresses
- **Success rate** from analysis
- **Metadata** (suggestions, scores, iteration info)

### 3. Prompt Retrieval

Before running OpenClaw, the system:

1. Determines task type from goal
2. Searches Redis for relevant prompts:
   - By task type (indexed)
   - By context similarity (keyword overlap)
   - By success rate (minimum threshold)
3. Scores candidates by:
   - Context match (exact matches get high score)
   - Keyword overlap
   - Problem pattern relevance
   - Success rate
   - Usage count (more used = more trusted)
4. Returns top result as a "tool" for OpenClaw

### 4. Prompt Tool Format

Retrieved prompts are formatted as:

```
LEARNED PROMPT TOOL (from past successful runs):

Task Context: Extract pricing data from shopbiolinkdepot.org...

Improved Prompt Strategy:
[The improved prompt with suggestions]

Problems This Addresses:
- missing_search: google, search, bing
- incomplete_output: json, file, save

Success Rate: 85%
Usage Count: 3

Apply this strategy to your current task.
```

This is automatically injected into the OpenClaw goal before execution.

## Usage

### Automatic (Integrated)

The system works automatically:
- Prompts are stored after successful beach runs
- Relevant prompts are retrieved and injected before execution
- No manual intervention needed

### Manual Query

Query stored prompts via API:

```bash
# List all prompts
GET /api/prompts

# Filter by task type
GET /api/prompts?task_type=pricing_extraction&limit=10
```

### Programmatic Access

```python
from rvla.prompt_database import get_prompt_database

db = get_prompt_database()

# Find relevant prompts
prompts = db.find_relevant_prompts(
    task_context="Extract prices from shopbiolinkdepot.org",
    task_type="pricing_extraction",
    min_success_rate=0.7,
    limit=5,
)

# Get prompt tool for OpenClaw
tool = db.get_prompt_tool_for_openclaw(
    task_context="Extract pricing data",
    task_type="pricing_extraction",
)
```

## Testing

Run the test script:

```bash
python scripts/test_prompt_database.py
```

This tests:
- Database initialization
- Prompt creation and storage
- Prompt retrieval
- Context-based search
- Prompt tool generation
- Usage tracking

## Configuration

### Redis Connection

Set `REDIS_URL` environment variable:

```bash
REDIS_URL=redis://:password@host:port/db
```

If Redis is unavailable, the system falls back to in-memory storage (data lost on restart).

### Task Types

Currently supported task types:
- `pricing_extraction`: Price extraction and comparison tasks
- `general`: Default for other tasks

Add more task types in `api/main.py`:

```python
task_type = "pricing_extraction" if "shopbiolinkdepot" in goal.lower() else "general"
```

## Benefits

1. **Self-Improvement**: System learns from past runs automatically
2. **Context-Aware**: Retrieves relevant prompts based on task similarity
3. **Persistent Learning**: Redis storage persists across restarts
4. **Transparent**: All learned prompts are queryable and inspectable
5. **Automatic**: No manual prompt engineering needed

## Example Flow

1. **First Run**: OpenClaw fails to search Google
   - Analysis identifies `missing_search` problem
   - Suggestion: "Add explicit web search steps"
   - Score: 0.65

2. **Second Run (Cook Longer)**: Suggestion applied
   - OpenClaw performs searches
   - Score: 0.85
   - **Prompt stored in Redis** with problem pattern

3. **Third Run (New Similar Task)**: 
   - System retrieves learned prompt from Redis
   - Injects it as a tool into the goal
   - OpenClaw uses the learned strategy immediately
   - Better performance from the start

## Integration Points

- **`api/main.py`**: 
  - `_stream_openclaw()`: Stores prompts after successful runs
  - `openclaw_beach()`: Retrieves prompts before execution
  - `openclaw_sea()`: Retrieves prompts before execution

- **`src/rvla/prompt_database.py`**:
  - Core database implementation
  - Pattern extraction from Weave traces
  - Context-based retrieval

## Future Enhancements

1. **Semantic Search**: Use embeddings for better context matching
2. **Prompt Versioning**: Track prompt evolution over time
3. **A/B Testing**: Compare different prompt strategies
4. **Prompt Merging**: Combine multiple successful prompts
5. **Weave Integration**: Direct query of Weave traces for pattern extraction
