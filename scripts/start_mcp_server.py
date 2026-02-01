"""Start the RLM-VLA MCP server.

This exposes your agent's capabilities so OpenClaw and other agents can call it.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rvla.mcp_server import main

if __name__ == "__main__":
    main()
