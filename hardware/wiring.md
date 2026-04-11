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

## UART (Serial to Mac)

Used by hook scripts to send notifications to the Pico.

| Signal | Pico Pin | GPIO |
|--------|----------|------|
| TX     | Pin 1    | GP0  |
| RX     | Pin 2    | GP1  |
| GND    | Pin 3    | GND  |

> Note: On macOS the Pico also appears as a serial port over USB
> (`/dev/tty.usbmodem*`). You can use that instead of the UART pins
> to keep the wiring simpler — just remove the UART lines from main.py
> and use the USB serial port directly in the hook scripts.

## Power

The Pico is powered entirely from the USB cable connected to the Mac.
No separate power supply needed.
