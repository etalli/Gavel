"""
Shared helpers for Gavel hook scripts.
Handles logging and serial communication with the Pico.
"""
import json
import os
import datetime
from typing import Optional

from find_device import find_pico_port

LOG_FILE      = os.path.join(os.path.dirname(__file__), "hook.log")
DECISIONS_LOG = os.path.expanduser("~/.claude/gavel/decisions.jsonl")


def log(event: str, payload: dict, port: Optional[str]) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    device = port if port else "no device"
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {event} → {json.dumps(payload)}  (port: {device})\n")


def _log_button_events(raw: str) -> None:
    """Parse button event JSON lines from the Pico and append to decisions log."""
    os.makedirs(os.path.dirname(DECISIONS_LOG), exist_ok=True)
    ts = datetime.datetime.now().isoformat()
    with open(DECISIONS_LOG, "a") as f:
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
                if evt.get("event") == "button":
                    evt["ts"] = ts
                    f.write(json.dumps(evt) + "\n")
            except (json.JSONDecodeError, KeyError):
                pass


def send_to_pico(event: str, payload: dict) -> None:
    """Find the Pico and send payload as JSON over serial. Logs errors only."""
    port = find_pico_port()
    if not port:
        return
    try:
        import serial
        with serial.Serial(port, timeout=1) as ser:  # baud rate is irrelevant over USB CDC
            ser.write((json.dumps(payload) + "\n").encode())
            # Drain any button events the Pico buffered since the last hook call
            if ser.in_waiting:
                _log_button_events(ser.read(ser.in_waiting).decode("utf-8", errors="replace"))
    except Exception as e:
        log(event, {"error": str(e)}, port)
