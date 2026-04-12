#!/usr/bin/env python3
"""
Claude Code hook: PostToolUse event
Tells the Pico to return to idle (all LEDs off) after a tool completes.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from pico import send_to_pico


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}

    tool_name = data.get("tool_name", "unknown")
    send_to_pico("PostToolUse", {"type": "idle", "tool": tool_name})


if __name__ == "__main__":
    main()
