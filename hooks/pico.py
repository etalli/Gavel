"""
Shared helpers for Gavel hook scripts.
Handles logging and serial communication with the Pico.
"""
import json
import os
import datetime
from typing import Optional

from find_device import find_pico_port

LOG_FILE = os.path.join(os.path.dirname(__file__), "hook.log")
BAUD_RATE = 9600


def log(event: str, payload: dict, port: Optional[str]) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    device = port if port else "no device"
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {event} → {json.dumps(payload)}  (port: {device})\n")


def send_to_pico(event: str, payload: dict) -> None:
    """Find the Pico and send payload as JSON over serial. Logs errors only."""
    port = find_pico_port()
    if not port:
        return
    try:
        import serial
        with serial.Serial(port, BAUD_RATE, timeout=1) as ser:
            ser.write((json.dumps(payload) + "\n").encode())
    except Exception as e:
        log(event, {"error": str(e)}, port)
