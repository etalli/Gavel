#!/usr/bin/env python3
"""
Claude Code hook: PreToolUse event
Lights up all three LEDs on the Pico to signal "waiting for approval".
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
    send_to_pico("PreToolUse", {"type": "permission", "tool": tool_name})


if __name__ == "__main__":
    main()
