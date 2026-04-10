"""
Utility: find the CCKN Pico's serial port on macOS.
"""
import glob
from typing import Optional


def find_pico_port() -> Optional[str]:
    """Return the first matching serial port for the Pico, or None."""
    candidates = (
        glob.glob("/dev/tty.usbmodem*")
        + glob.glob("/dev/tty.usbserial*")
        + glob.glob("/dev/cu.usbmodem*")
    )
    return candidates[0] if candidates else None
