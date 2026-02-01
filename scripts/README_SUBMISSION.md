# Hackathon Submission Autopilot

This script showcases the RLM-VLA agent's capabilities by generating complete hackathon submission materials from your repo.

## What It Does

1. **Reads entire repo** (ultralong context handling)
2. **Analyzes documentation** and code structure
3. **Generates submission pack**:
   - `submission.json` - Form-ready fields
   - `DEMO.md` - 3-5 minute demo script
   - `SPONSORS.md` - Sponsor tool usage
   - `HACKATHON_LEDGER.md` - What was built
   - `SOCIAL_POST.md` - Ready-to-share post
   - `SUMMARY.md` - Quick overview
4. **Self-improves** until it passes hard checks
5. **Traces everything to Weave**

## Usage

```bash
# Set environment variables
export OPENAI_API_KEY=your_key
export WANDB_API_KEY=your_key
export WANDB_ENTITY=your_entity
export WANDB_PROJECT=weavehacks-rvla

# Generate submission pack
python scripts/generate_submission_pack.py

# Output will be in submission_pack/
```

## Demo Flow

1. Run the script
2. Show it reading the repo (it's using RLM for ultralong context!)
3. Show Weave trace of the generation process
4. Open `submission_pack/DEMO.md` and follow it live
5. Show the self-improvement iterations in Weave

## Why This Is Badass

- **Proves your agent works**: It's using your own agent to generate its submission
- **Showcases RLM**: Handles entire repo context (100+ files)
- **Self-improving**: Iterates until it passes checks
- **Fully traced**: Every step in Weave
- **Immediately useful**: Actually generates your submission
