# RLM-VLA: Recursive Language Model for Vision-Language-Action

A hackathon project implementing [Recursive Language Models (RLM)](https://arxiv.org/abs/2512.24601) for Vision-Language-Action (VLA) tasks with ultralong context handling.

## Features

- **RLM Core**: Programmatic context examination for contexts 2 orders of magnitude beyond model limits
- **GPT-4o Vision**: Visual analysis and planning with screenshot understanding
- **Browserbase Integration**: Real browser automation
- **Multi-Agent Coordination**: Works with OpenClaw, Gastown, and other MCP agents
- **Weave Tracing**: All operations traced with W&B Weave
- **Redis Memory**: External workspace for ultralong context
- **Self-Improvement**: Prompt optimization based on Weave traces

## Architecture

```
RLM-VLA Agent
├─ Vision: GPT-4o analyzes screenshots
├─ Language: GPT-4o plans actions
├─ Action: Browserbase executes browser commands
├─ RLM: Examines long context programmatically
├─ Weave: Traces all operations
└─ Redis: Stores context externally
```

## Quick Start

```bash
# Install dependencies
pip install -e .

# Set up environment
cp .env.example .env
# Add your API keys to .env

# Run demo
python scripts/run_demo.py
```

## Environment Variables

```bash
# Required
OPENAI_API_KEY=your_key
WANDB_API_KEY=your_key
WANDB_PROJECT=weavehacks-rvla
WANDB_ENTITY=your_entity

# Optional
REDIS_URL=redis://...
BROWSERBASE_API_KEY=your_key
BROWSERBASE_PROJECT_ID=your_id
```

## Project Structure

```
src/rvla/
├── agent.py              # Main agent loop
├── llm.py                # GPT-4o planning and vision
├── rlm_core.py           # RLM context examination
├── visual_rlm.py           # Visual snippet processing
├── memory.py            # Redis/in-memory workspace
├── web.py               # Browserbase integration
├── multi_agent_coordinator.py  # OpenClaw/Gastown coordination
├── self_improvement.py  # Prompt optimization
└── weave_init.py        # Ensures Weave is always initialized
```

## Weave Integration

**All traces are automatically logged to Weave.** The `weave_init.py` module ensures Weave is initialized before any operations, so every `@weave.op()` decorated function is traced.

View traces at: `https://wandb.ai/{entity}/{project}/weave`

## Multi-Agent Coordination

Works with:
- **OpenClaw**: File operations, calendar, email
- **Gastown**: Workflow orchestration
- **Any MCP agent**: Via Model Context Protocol

## License

MIT

## Hackathon

Built for WeaveHacks 3 - demonstrating RLM for ultralong context VLA tasks.
