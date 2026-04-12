"""
Gavel – LED test script

Cycles through each LED independently to verify wiring.
  GP10 (green) → GP11 (green) → GP12 (red) → repeat

Copy this file to the CIRCUITPY drive as code.py to run the test.
Restore the original code.py when done.
"""

import board
import digitalio
import time

def make_led(pin):
    led = digitalio.DigitalInOut(pin)
    led.direction = digitalio.Direction.OUTPUT
    led.value = False
    return led

led_allow_once   = make_led(board.GP10)  # green
led_always_allow = make_led(board.GP11)  # green
led_reject       = make_led(board.GP12)  # red

leds = [
    (led_allow_once,   "GP10 - Allow Once   (green)"),
    (led_always_allow, "GP11 - Always Allow (green)"),
    (led_reject,       "GP12 - Reject       (red)"),
]

print("LED test starting...")

while True:
    for led, label in leds:
        print("ON:", label)
        led.value = True
        time.sleep(1.0)
        led.value = False
        time.sleep(0.3)
