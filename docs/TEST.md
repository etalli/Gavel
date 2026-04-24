# Gavel Kit Test Checklist

Work through each section in order. All steps must pass before shipping or using the device.

---

## 1. PCB Inspection (Before Soldering)

Visual checks before applying any heat:

- [ ] No visible shorts between adjacent pads (use a magnifier if needed)
- [ ] All pads are clean — no oxidation or solder mask damage
- [ ] Top plate aligns correctly over the main PCB

---

## 2. Firmware Flash

**Goal:** Confirm the RP2040-Zero accepts firmware.

1. Hold the **BOOT** button on the RP2040-Zero
2. Plug the USB cable into your Mac while holding BOOT
3. Release BOOT — a drive named `RPI-RP2` should appear in Finder
4. Drag the CircuitPython `.uf2` file onto `RPI-RP2`
5. The drive will disappear and reappear as `CIRCUITPY`

- [ ] `RPI-RP2` appears when entering bootloader mode
- [ ] `CIRCUITPY` drive mounts after flashing

---

## 3. Library and Firmware Files

Copy required files to `CIRCUITPY`:

| File / Folder | Destination |
|---|---|
| `adafruit_hid/` | `CIRCUITPY/lib/adafruit_hid/` |
| `neopixel.mpy` | `CIRCUITPY/lib/neopixel.mpy` |
| `firmware/boot.py` | `CIRCUITPY/boot.py` |
| `firmware/code.py` | `CIRCUITPY/code.py` |

After copying, **power cycle** (unplug and replug USB).

- [ ] All files copied without error
- [ ] Board reboots cleanly after power cycle

---

## 4. LED Self-Test (Idle State)

With the board powered and `code.py` running:

- [ ] The built-in RGB NeoPixel lights up **white** (waiting for input state)

If the LED stays off or shows an unexpected color, confirm your board is a supported NeoPixel board — board type is auto-detected from the board ID.

---

## 5. Button Test — USB HID

**Goal:** Each button sends the correct keypress to the Mac.

1. Open any text editor on your Mac (e.g., TextEdit)
2. Click inside the document so it has focus
3. Press each button on Gavel one at a time

| Button | Expected keypress | Expected LED color |
|---|---|---|
| Allow Once | `1` | Green |
| Always Allow | `2` | Blue |
| Reject | `3` | Red |

- [ ] Allow Once sends `1` and LED turns green
- [ ] Always Allow sends `2` and LED turns blue
- [ ] Reject sends `3` and LED turns red
- [ ] LED returns to white after ~1 second

---

## 6. Serial Port Detection

**Goal:** Confirm the Mac can see both USB serial ports.

Run in Terminal:

```sh
ls /dev/tty.usbmodem*
```

Expected output: two ports, for example:

```
/dev/tty.usbmodem1101
/dev/tty.usbmodem1103
```

- [ ] Two `tty.usbmodem*` ports appear

---

## 7. Hook Integration Test

**Goal:** Confirm Claude Code hooks trigger LED responses.

1. Run `./install.sh --deploy` to register hooks
2. Start a Claude Code session
3. Ask Claude to run any tool (e.g., `list files`)

| Hook event | Expected LED behavior |
|---|---|
| `PreToolUse` (permission prompt) | All LEDs solid on |
| `PostToolUse` (after tool runs) | All LEDs off → return to white |
| `Notification` (warn) | Three medium flashes |
| `Notification` (error) | Five fast red flashes |

- [ ] LED responds to `PreToolUse`
- [ ] LED responds to `PostToolUse`
- [ ] Notification events produce correct flash patterns

---

## 8. Reset Button Test

1. Press the **RESET** button on the RP2040-Zero
2. The board should reboot and the NeoPixel should return to white within 3 seconds

- [ ] Reset button reboots the board cleanly
- [ ] Firmware restarts without needing to replug USB

---

## Pass Criteria

All checkboxes above must be checked before the kit is considered ready to ship or use.

If any step fails, refer to [`hardware/wiring.md`](hardware/wiring.md) for pin assignments and [`README.md`](README.md) for setup instructions.
