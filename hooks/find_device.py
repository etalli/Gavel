"""
Utility: find the Gavel Pico's serial port on macOS.
"""
import glob
from typing import Optional


def find_pico_port() -> Optional[str]:
    """Return the data serial port for the Pico (highest-numbered usbmodem), or None.

    CircuitPython with usb_cdc.enable(console=True, data=True) creates two ports:
      tty.usbmodem*1  → REPL console
      tty.usbmodem*3  → data port (what we want)
    """
    candidates = sorted(
        glob.glob("/dev/tty.usbmodem*")
        + glob.glob("/dev/tty.usbserial*")
    )
    return candidates[-1] if candidates else None
