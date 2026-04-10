#!/usr/bin/env python3
"""
Claude Code hook: Notification event
Called by Claude Code when a notification fires.

Usage (configured in .claude/settings.json):
  command: "python3 /path/to/hooks/notify.py"

Claude Code passes notification data via environment variables or stdin.
This script reads the hook input from stdin (JSON) and forwards it to the Pico.
"""
import json
import sys
import os
import datetime
from typing import Optional

# Allow importing find_device from the same folder regardless of cwd
sys.path.insert(0, os.path.dirname(__file__))
from find_device import find_pico_port

LOG_FILE = os.path.join(os.path.dirname(__file__), "hook.log")


def log(event: str, payload: dict, port: Optional[str]) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    device = port if port else "no device"
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {event} → {json.dumps(payload)}  (port: {device})\n")


def send_to_pico(payload: dict) -> None:
    port = find_pico_port()
    log("Notification", payload, port)
    if not port:
        return
    try:
        import serial
        with serial.Serial(port, 9600, timeout=1) as ser:
            ser.write((json.dumps(payload) + "\n").encode())
    except Exception:
        pass


def main():
    # Claude Code sends hook data as JSON on stdin
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}

    message = data.get("message", "")
    level = "info"
    if any(w in message.lower() for w in ("error", "fail", "fatal")):
        level = "error"
    elif any(w in message.lower() for w in ("warn", "caution")):
        level = "warn"

    send_to_pico({"type": "notification", "level": level, "message": message})


if __name__ == "__main__":
    main()
