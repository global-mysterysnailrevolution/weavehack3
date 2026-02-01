"""Centralized Weave initialization to ensure traces are always logged."""

import os
import sys
from typing import Optional

import weave
from dotenv import load_dotenv

# Load env on import
load_dotenv()

_weave_initialized = False


def ensure_weave_init(project: Optional[str] = None, entity: Optional[str] = None) -> None:
    """Ensure Weave is initialized. Safe to call multiple times.
    
    This ensures traces are ALWAYS logged to a Weave project.
    """
    global _weave_initialized
    
    if _weave_initialized:
        return
    
    # Get project and entity from env or parameters
    project_name = project or os.getenv("WANDB_PROJECT", "weavehacks-rvla")
    entity_name = entity or os.getenv("WANDB_ENTITY")
    
    # Format: "entity/project" or just "project"
    if entity_name:
        full_project_name = f"{entity_name}/{project_name}"
    else:
        full_project_name = project_name
    
    # Initialize Weave
    try:
        weave.init(full_project_name)
        _weave_initialized = True
        # Only print if not in quiet mode (MCP servers need quiet stdout)
        if not os.getenv("WEAVE_QUIET"):
            print(f"[WEAVE] Initialized: {full_project_name}", file=sys.stderr)
    except Exception as e:
        if not os.getenv("WEAVE_QUIET"):
            print(f"[WARN] Weave initialization failed: {e}", file=sys.stderr)
        # Try to initialize anyway with minimal config
        try:
            weave.init(project_name)
            _weave_initialized = True
        except:
            pass


# Auto-initialize on import
ensure_weave_init()
