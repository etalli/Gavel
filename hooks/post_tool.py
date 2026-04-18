#!/usr/bin/env python3
"""
Claude Code hook: PostToolUse event
Tells the Pico to return to idle (all LEDs off) after a tool completes.
If context window usage is near full, flashes a warning first.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from pico import send_to_pico

USAGE_WARN_THRESHOLD = 0.9  # warn when context window is 90%+ full


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}

    tool_name = data.get("tool_name", "unknown")
    usage = data.get("context_window_utilization", 0.0)

    if usage >= USAGE_WARN_THRESHOLD:
        send_to_pico("PostToolUse/UsageWarn", {"type": "notification", "level": "warn"})

    send_to_pico("PostToolUse", {"type": "idle", "tool": tool_name})


if __name__ == "__main__":
    main()
