# Gavel Wiring Reference

## Buttons

Each button connects between a GPIO pin and GND.
The firmware uses the Pico's internal pull-up — no external resistor needed.

| Button       | Pico Pin | GPIO |
|--------------|----------|------|
| Allow Once   | Pin 4    | GP2  |
| Always Allow | Pin 5    | GP3  |
| Reject       | Pin 6    | GP4  |

Wiring per button:
```
GPIO pin ──[button]── GND
```

## LEDs

Each LED needs a 220Ω resistor in series.

| LED          | Pico Pin | GPIO | Color |
|--------------|----------|------|-------|
| Allow Once   | Pin 14   | GP10 | Green |
| Always Allow | Pin 15   | GP11 | Green |
| Reject       | Pin 16   | GP12 | Red   |

Wiring per LED:
```
GPIO pin ──[220Ω]──[LED anode → cathode]── GND
```

## Reset Button

Connecting a momentary button between the RUN pin and GND resets the firmware without unplugging USB.

| Button | Pico Pin | Notes |
|--------|----------|-------|
| Reset  | Pin 30 (RUN) | Connect to GND momentarily |

No resistor needed — the Pico has an internal pull-up on RUN.

```
RUN (Pin 30) ──[button]── GND
```

## Serial (USB)

The Pico communicates with the Mac over USB — no extra wires needed.

CircuitPython's `usb_cdc` exposes two serial ports over the same USB cable:

| Port | Purpose |
|------|---------|
| `/dev/tty.usbmodem*1` | REPL console |
| `/dev/tty.usbmodem*2` | Data port used by hook scripts |

The hook scripts on the Mac write JSON commands to the data port; the firmware reads them and controls the LEDs.

## Power

The Pico is powered entirely from the USB cable connected to the Mac.
No separate power supply needed.
