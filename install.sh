#!/bin/bash
# Install Gavel firmware to the Raspberry Pi Pico (CIRCUITPY drive).
# Uses cp instead of Finder drag-and-drop to avoid the "-1.py" rename issue.

set -e

CIRCUITPY="/Volumes/CIRCUITPY"
FIRMWARE="$(dirname "$0")/firmware"

if [ ! -d "$CIRCUITPY" ]; then
    echo "ERROR: CIRCUITPY drive not found. Plug in the Pico and try again."
    exit 1
fi

echo "Installing firmware to $CIRCUITPY ..."

cp -v "$FIRMWARE/boot.py"  "$CIRCUITPY/boot.py"
cp -v "$FIRMWARE/code.py"  "$CIRCUITPY/code.py"

echo "Done. The Pico will reboot automatically."
