# Execution Plan (RVLA Web-Navigator)

## Objective
Build a hackathon-ready scaffold for a **Recursive VLA web agent** that uses Weave trace trees to visualize recursive decomposition and external memory access.

## Constraints
- Short build window (hackathon).
- External services (Browserbase/Stagehand, Redis, Gemini) may not be configured yet.
- Weave tracing should be first-class and visible even in stubbed mode.

## Milestones
1. **Scaffold**: repo structure, docs, and dependency setup.
2. **Core ops**: implement recursive ops with Weave decorators.
3. **Workspace**: external memory with Redis fallback.
4. **Demo**: run a lightweight simulated task to generate a trace tree.
5. **Integration hooks**: clear interfaces for browser actions + model calls.

## Tasks
- [ ] Initialize Python package (rvla).
- [ ] Implement Workspace with Redis support and in-memory fallback.
- [ ] Implement @weave.op functions: step, inspect_history, crop, subcall, score.
- [ ] Provide WebDriver interface for browser actions.
- [ ] Add a demo runner script that exercises recursion.
- [ ] Document environment variables and next steps.

## Risks & Mitigations
- **Risk:** Missing external services (Stagehand, Redis, models).
  - **Mitigation:** Provide stubbed implementations and clean integration points.
- **Risk:** Weave config not set.
  - **Mitigation:** Use environment variables and print onboarding hints.

## Success Criteria
- Running scripts/run_demo.py produces a Weave trace tree with nested calls.
- The demo shows at least one recursive subcall path.

