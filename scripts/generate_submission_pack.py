"""Hackathon Submission Autopilot: Generates submission materials from repo + Weave traces.

This showcases the RLM-VLA agent's capabilities:
- Reads entire repo context (ultralong context handling)
- Analyzes Weave traces for what was built
- Generates submission materials
- Self-improves until it passes hard checks
"""

import argparse
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

import weave

# Ensure Weave is initialized
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

from openai import OpenAI


def run_cmd(cmd: list[str]) -> str:
    """Run shell command and return output."""
    try:
        return subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, text=True, shell=True
        ).strip()
    except Exception as e:
        return f"Error: {e}"


def read_file_safe(p: Path, max_bytes: int = 400_000) -> str:
    """Read file with size limit."""
    try:
        data = p.read_bytes()
        if len(data) > max_bytes:
            data = data[:max_bytes]
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def collect_repo_context(repo_root: Path) -> dict[str, Any]:
    """Collect high-signal files and metadata from repo."""
    # Key documentation files
    doc_files = [
        "README.md",
        "PLAN.md",
        "HACKATHON_PLAN.md",
        "RLM_IMPLEMENTATION.md",
        "VLA_ARCHITECTURE.md",
        "SELF_IMPROVEMENT_EXPLAINED.md",
        "MULTI_AGENT_INTEGRATION.md",
        "CONTEXT_ANALYSIS.md",
        "WEB_UI_SUMMARY.md",
        "DEPLOYMENT.md",
    ]
    
    # Config files
    config_files = [
        "pyproject.toml",
        "Procfile",
        "railway.json",
        "nixpacks.toml",
    ]
    
    files = {}
    for rel in doc_files + config_files:
        p = repo_root / rel
        if p.exists() and p.is_file():
            files[rel] = read_file_safe(p)
    
    # Get repo structure
    try:
        tree = run_cmd("find src web api examples -type f -name '*.py' -o -name '*.tsx' -o -name '*.ts' | head -50")
    except Exception:
        tree = "Could not generate tree"
    
    # Get git log since Saturday (hackathon start)
    try:
        git_log = run_cmd("git log --since='2026-01-31 00:00' --pretty=format:'%h %ad %s' --date=short")
    except Exception:
        git_log = "No git log available"
    
    # Get commit count
    try:
        commit_count = run_cmd("git rev-list --count HEAD")
    except Exception:
        commit_count = "unknown"
    
    return {
        "tree": tree,
        "files": files,
        "git_log": git_log,
        "commit_count": commit_count,
    }


@weave.op()
def llm_json(system: str, user: str, model: str = "gpt-4o-mini") -> dict[str, Any]:
    """Call LLM and return JSON."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content or "{}")


@weave.op()
def llm_text(system: str, user: str, model: str = "gpt-4o") -> str:
    """Call LLM and return text."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.4,
    )
    return resp.choices[0].message.content or ""


def hard_check(pack: dict[str, Any]) -> dict[str, Any]:
    """Non-LLM scorer: judges care about completeness + specificity."""
    required_fields = [
        "team_name",
        "project_name",
        "summary",
        "utility",
        "how_built",
        "sponsor_tools",
        "weave_link",
        "github_link",
    ]
    missing = [k for k in required_fields if not pack.get(k)]
    
    sponsor_tools = pack.get("sponsor_tools") or []
    sponsor_ok = isinstance(sponsor_tools, list) and len(sponsor_tools) >= 2
    
    demo = (pack.get("demo_script") or "").strip()
    demo_ok = 250 <= len(demo) <= 2000  # 3-5 minutes spoken
    
    summary = (pack.get("summary") or "").strip()
    summary_ok = 100 <= len(summary) <= 500
    
    return {
        "missing_fields": missing,
        "sponsor_ok": sponsor_ok,
        "demo_ok": demo_ok,
        "summary_ok": summary_ok,
        "pass": (len(missing) == 0 and sponsor_ok and demo_ok and summary_ok),
    }


@weave.op()
def generate_submission_pack(context: dict[str, Any], meta: dict[str, Any], model: str) -> dict[str, Any]:
    """Generate hackathon submission pack from repo context."""
    system = """You generate hackathon submission packs for WeaveHacks 3.
Return JSON only with these exact fields:
- team_name: string
- project_name: string
- summary: string (100-500 chars, what the project does)
- utility: string (why it's useful)
- how_built: string (technical architecture, be specific)
- sponsor_tools: array of {name: string, how_used: string}
- github_link: string
- weave_link: string
- demo_script: string (3-5 minute demo walkthrough, click-by-click)
- hackathon_ledger: string (what was built during hackathon, reference commits)
- social_post: string (X/Twitter post ready to share)

Be specific about architecture, dataflow, and exactly how sponsor tools were used.
Reference actual files and commits from the repo context."""
    
    user = f"""Hackathon meta:
- Event: WeaveHacks 3
- Repo URL: {meta["github_link"]}
- Weave: {meta["wandb_entity"]}/{meta["wandb_project"]}
- Generated: {meta["generated_at"]}

Repo structure:
{context["tree"]}

Recent commits (hackathon ledger):
{context["git_log"]}

Total commits: {context["commit_count"]}

Key documentation:
{json.dumps(context["files"], ensure_ascii=False)[:150000]}

Generate a complete submission pack. Be specific and truthful to what's actually in the repo."""
    
    return llm_json(system, user, model=model)


@weave.op()
def repair_pack(pack: dict[str, Any], checks: dict[str, Any], model: str) -> dict[str, Any]:
    """Repair submission pack to pass checks."""
    system = """You repair hackathon submission JSON to satisfy hard checks.
Return the complete fixed JSON."""
    
    user = f"""Current submission pack:
{json.dumps(pack, indent=2)}

Checks that failed:
{json.dumps(checks, indent=2)}

Fix the JSON so it passes all checks. Keep it specific and truthful."""
    
    return llm_json(system, user, model=model)


def write_outputs(out_dir: Path, pack: dict[str, Any], checks: dict[str, Any]) -> None:
    """Write all output files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Main submission JSON
    (out_dir / "submission.json").write_text(
        json.dumps(pack, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    # Demo script
    (out_dir / "DEMO.md").write_text(
        pack.get("demo_script", ""),
        encoding="utf-8"
    )
    
    # Sponsor tools
    sponsors = pack.get("sponsor_tools") or []
    sponsors_md = "\n".join([
        f"### {s.get('name', 'Unknown')}\n{s.get('how_used', '')}\n"
        for s in sponsors
    ])
    (out_dir / "SPONSORS.md").write_text(sponsors_md, encoding="utf-8")
    
    # Hackathon ledger
    (out_dir / "HACKATHON_LEDGER.md").write_text(
        pack.get("hackathon_ledger", ""),
        encoding="utf-8"
    )
    
    # Social post
    (out_dir / "SOCIAL_POST.md").write_text(
        pack.get("social_post", ""),
        encoding="utf-8"
    )
    
    # Checks result
    (out_dir / "CHECKS.json").write_text(
        json.dumps(checks, indent=2),
        encoding="utf-8"
    )
    
    # Quick summary
    summary = f"""# {pack.get('project_name', 'Project')}

**Team:** {pack.get('team_name', 'Unknown')}

## Summary
{pack.get('summary', '')}

## Utility
{pack.get('utility', '')}

## How Built
{pack.get('how_built', '')}

## Links
- GitHub: {pack.get('github_link', '')}
- Weave: {pack.get('weave_link', '')}
"""
    (out_dir / "SUMMARY.md").write_text(summary, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Generate hackathon submission pack from repo + Weave traces"
    )
    parser.add_argument("--repo", default=".", help="Path to repo root")
    parser.add_argument("--out", default="submission_pack", help="Output directory")
    parser.add_argument("--model", default=os.getenv("SUBMISSION_MODEL", "gpt-4o-mini"))
    parser.add_argument("--wandb_entity", default=os.getenv("WANDB_ENTITY", ""))
    parser.add_argument("--wandb_project", default=os.getenv("WANDB_PROJECT", "weavehacks-rvla"))
    parser.add_argument("--max_iters", type=int, default=3, help="Max repair iterations")
    args = parser.parse_args()
    
    # Initialize Weave
    project_name = args.wandb_project
    if args.wandb_entity:
        project_name = f"{args.wandb_entity}/{project_name}"
    weave.init(project_name)
    
    repo_root = Path(args.repo).resolve()
    out_dir = Path(args.out).resolve()
    
    print("[INFO] Collecting repo context...")
    context = collect_repo_context(repo_root)
    
    # Get GitHub URL
    github_url = run_cmd("git config --get remote.origin.url")
    if not github_url or github_url.startswith("Error"):
        github_url = "https://github.com/global-mysterysnailrevolution/weavehack3"
    if github_url.endswith(".git"):
        github_url = github_url[:-4]
    if github_url.startswith("git@"):
        github_url = github_url.replace(":", "/").replace("git@", "https://")
    
    meta = {
        "github_link": github_url,
        "wandb_entity": args.wandb_entity,
        "wandb_project": args.wandb_project,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    print("[INFO] Generating submission pack...")
    pack = {}
    checks = {"pass": False}
    
    for i in range(args.max_iters):
        print(f"[INFO] Iteration {i+1}/{args.max_iters}...")
        
        if i == 0:
            pack = generate_submission_pack(context, meta, model=args.model)
        else:
            pack = repair_pack(pack, checks, model=args.model)
        
        # Ensure links are present
        pack.setdefault("github_link", meta["github_link"])
        pack.setdefault("weave_link", f"https://wandb.ai/{args.wandb_entity}/{args.wandb_project}/weave")
        
        checks = hard_check(pack)
        pack["_checks"] = checks
        
        if checks["pass"]:
            print("[SUCCESS] Submission pack passes all checks!")
            break
        else:
            print(f"[INFO] Checks failed: {checks}")
    
    print(f"[INFO] Writing outputs to {out_dir}...")
    write_outputs(out_dir, pack, checks)
    
    print("\n" + "="*70)
    print("✅ SUBMISSION PACK GENERATED")
    print("="*70)
    print(f"Output directory: {out_dir}")
    print(f"Checks passed: {checks['pass']}")
    if not checks["pass"]:
        print(f"Missing fields: {checks.get('missing_fields', [])}")
    print("\nFiles generated:")
    for f in out_dir.glob("*"):
        print(f"  - {f.name}")
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
