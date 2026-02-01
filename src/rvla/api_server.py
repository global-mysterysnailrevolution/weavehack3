"""API server for web UI integration.

This script runs the agent and outputs updates in a format
that can be consumed by the Next.js frontend via Server-Sent Events.
"""

import sys
import json
import os
from typing import Any

# Ensure Weave is initialized
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver


def format_update(update_type: str, data: dict[str, Any]) -> None:
    """Output an update in SSE format."""
    try:
        update_json = json.dumps({'type': update_type, **data})
        print(f"UPDATE:{update_json}", flush=True)
    except Exception as e:
        print(f"ERROR: Failed to format update: {e}", file=sys.stderr, flush=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: python api_server.py <goal>", file=sys.stderr)
        sys.exit(1)

    goal = sys.argv[1]

    # Initialize components
    workspace = workspace_from_env()
    driver = WebDriver()

    try:
        format_update('start', {'goal': goal})

        # Run agent with callback for updates
        result = run_agent(
            goal=goal,
            driver=driver,
            workspace=workspace,
            enable_multi_agent=True,
        )

        # Send periodic updates
        for i, action in enumerate(result['trajectory']):
            format_update('action', {
                'step': i + 1,
                'action': {
                    'type': action.type,
                    'payload': action.payload,
                    'timestamp': str(action.timestamp) if hasattr(action, 'timestamp') else '',
                },
            })

        format_update('observation', {
            'observation': {
                'url': result['last_observation'].url if result.get('last_observation') else '',
                'screenshot_base64': result['last_observation'].screenshot_base64 if result.get('last_observation') else None,
                'metadata': result['last_observation'].metadata if result.get('last_observation') else {},
            },
        })

        format_update('events', {'events': result['events']})

        format_update('complete', {
            'score': result.get('score', 0),
            'total_steps': len(result['trajectory']),
        })

    except Exception as e:
        format_update('error', {'error': str(e)})
        raise
    finally:
        driver.close()


if __name__ == '__main__':
    main()
