#!/usr/bin/env python
"""Wrapper script for MCP stdio server that Cursor can run."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import and run the server
from rvla.mcp_stdio_server import main

if __name__ == "__main__":
    main()
