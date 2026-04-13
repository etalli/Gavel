#!/bin/bash
# Gavel installer
#
# Usage:
#   ./install.sh           Install firmware to CIRCUITPY drive
#   ./install.sh --deploy  Copy hook scripts to ~/.claude/gavel/ and update settings.json

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FIRMWARE="$SCRIPT_DIR/firmware"
HOOKS="$SCRIPT_DIR/hooks"

# ── Deploy mode ────────────────────────────────────────────────────────────────
if [ "$1" = "--deploy" ]; then
    DEST="$HOME/.claude/gavel"
    SETTINGS="$HOME/.claude/settings.json"

    echo "Deploying hook scripts to $DEST ..."
    mkdir -p "$DEST"
    cp -v "$HOOKS/pico.py"        "$DEST/pico.py"
    cp -v "$HOOKS/find_device.py" "$DEST/find_device.py"
    cp -v "$HOOKS/pre_tool.py"    "$DEST/pre_tool.py"
    cp -v "$HOOKS/post_tool.py"   "$DEST/post_tool.py"
    cp -v "$HOOKS/notify.py"      "$DEST/notify.py"

    echo "Updating $SETTINGS ..."
    # Replace project-path hook commands with deployed path
    sed -i '' \
        "s|python3 .*/hooks/pre_tool.py|python3 $DEST/pre_tool.py|g" \
        "$SETTINGS"
    sed -i '' \
        "s|python3 .*/hooks/post_tool.py|python3 $DEST/post_tool.py|g" \
        "$SETTINGS"
    sed -i '' \
        "s|python3 .*/hooks/notify.py|python3 $DEST/notify.py|g" \
        "$SETTINGS"

    echo "Done. Hooks are now running from $DEST"
    exit 0
fi

# ── Firmware mode (default) ────────────────────────────────────────────────────
CIRCUITPY="/Volumes/CIRCUITPY"

if [ ! -d "$CIRCUITPY" ]; then
    echo "ERROR: CIRCUITPY drive not found. Plug in the Pico and try again."
    exit 1
fi

echo "Installing firmware to $CIRCUITPY ..."
cp -v "$FIRMWARE/boot.py" "$CIRCUITPY/boot.py"
cp -v "$FIRMWARE/code.py" "$CIRCUITPY/code.py"
echo "Done. The Pico will reboot automatically."
