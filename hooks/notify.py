#!/usr/bin/env python3
"""
Claude Code hook: Notification event
Forwards Claude Code notifications to the Pico as LED signals.
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

    message = data.get("message", "")
    if any(w in message.lower() for w in ("error", "fail", "fatal")):
        level = "error"
    elif any(w in message.lower() for w in ("warn", "caution")):
        level = "warn"
    else:
        level = "info"

    send_to_pico("Notification", {"type": "notification", "level": level, "message": message})


if __name__ == "__main__":
    main()
