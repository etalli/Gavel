#!/usr/bin/env python3
"""
Claude Code hook: PreToolUse event
Lights up LEDs on the Pico with a pattern based on tool risk category.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from pico import send_to_pico

READONLY_TOOLS = {"Read", "Glob", "Grep", "LS"}
WRITE_TOOLS    = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
NETWORK_TOOLS  = {"WebFetch", "WebSearch", "Agent"}


def classify(tool_name):
    if tool_name in READONLY_TOOLS:
        return "readonly"
    if tool_name in WRITE_TOOLS:
        return "write"
    if tool_name in NETWORK_TOOLS:
        return "network"
    return "destructive"


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}

    tool_name = data.get("tool_name", "unknown")
    category  = classify(tool_name)
    send_to_pico("PreToolUse", {"type": "permission", "tool": tool_name, "category": category})


if __name__ == "__main__":
    main()
