#!/usr/bin/env python3
"""
Claude Code hook: PostToolUse event
Tells the Pico to return to idle (all LEDs off) after a tool completes.

Usage (configured in .claude/settings.json):
  command: "python3 /path/to/hooks/post_tool.py"
"""
import json
import sys
import os
import datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
from find_device import find_pico_port

LOG_FILE = os.path.join(os.path.dirname(__file__), "hook.log")


def log(event: str, payload: dict, port: Optional[str]) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    device = port if port else "no device"
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {event} → {json.dumps(payload)}  (port: {device})\n")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}

    tool_name = data.get("tool_name", "unknown")
    payload = {"type": "idle", "tool": tool_name}

    port = find_pico_port()
    log("PostToolUse", payload, port)
    if not port:
        return

    try:
        import serial
        with serial.Serial(port, 9600, timeout=1) as ser:
            ser.write((json.dumps({"type": "idle"}) + "\n").encode())
    except Exception:
        pass


if __name__ == "__main__":
    main()
