# Gavel Wiring Reference

Both supported boards use the same GPIO numbers. Set `USE_NEOPIXEL` in `firmware/code.py` to match your board.

| Board | `USE_NEOPIXEL` | LED output |
|-------|---------------|------------|
| Raspberry Pi Pico | `False` | 3× discrete LEDs on GP10/GP11/GP12 |
| Waveshare RP2040 Zero | `True` | RGB NeoPixel on GP16 (built-in) |

---

## Buttons

Each button connects between a GPIO pin and GND.
The internal pull-up is used — no external resistor needed.

| Button       | GPIO |
|--------------|------|
| Allow Once   | GP2  |
| Always Allow | GP3  |
| Reject       | GP4  |

Wiring per button:
```
GPIO pin ──[button]── GND
```

## LEDs — Raspberry Pi Pico

Each LED needs a 220Ω resistor in series.

| LED          | Pico Pin | GPIO | Color |
|--------------|----------|------|-------|
| Allow Once   | Pin 14   | GP10 | Green |
| Always Allow | Pin 15   | GP11 | Green |
| Reject       | Pin 16   | GP12 | Red   |

```
GPIO pin ──[220Ω]──[LED anode → cathode]── GND
```

## LEDs — Waveshare RP2040 Zero

The RP2040 Zero has a built-in RGB NeoPixel on GP16. No external LEDs or resistors needed.

Color coding:

| Event | Color |
|-------|-------|
| Waiting for input | White |
| Allow Once pressed | Green |
| Always Allow pressed | Blue |
| Reject pressed | Red |
| Notification (info) | White pulse |
| Notification (warn) | Orange flash |
| Notification (error) | Red rapid flash |
| Breathing (idle, optional) | Red fade in/out |

## Reset Button

Connecting a momentary button between the RUN pin and GND resets the firmware without unplugging USB.

| Button | GPIO | Notes |
|--------|------|-------|
| Reset  | RUN (Pin 30 on Pico) | Connect to GND momentarily |

No resistor needed — internal pull-up on RUN.

```
RUN ──[button]── GND
```

## Serial (USB)

The board communicates with the Mac over USB — no extra wires needed.

CircuitPython's `usb_cdc` exposes two serial ports over the same USB cable:

| Port | Purpose |
|------|---------|
| `/dev/tty.usbmodem*1` | REPL console |
| `/dev/tty.usbmodem*2` | Data port used by hook scripts |

The hook scripts on the Mac write JSON commands to the data port; the firmware reads them and controls the LEDs.

## Power

The Pico is powered entirely from the USB cable connected to the Mac.
No separate power supply needed.
