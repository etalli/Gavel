"""
Gavel – LED test script

Cycles through each LED independently to verify wiring.
  GP2 (green) → GP3 (green) → GP4 (red) → repeat

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

led_allow_once   = make_led(board.GP2)  # green
led_always_allow = make_led(board.GP3)  # green
led_reject       = make_led(board.GP4)  # red

leds = [
    (led_allow_once,   "GP2 - Allow Once   (green)"),
    (led_always_allow, "GP3 - Always Allow (green)"),
    (led_reject,       "GP4 - Reject       (red)"),
]

print("LED test starting...")

while True:
    for led, label in leds:
        print("ON:", label)
        led.value = True
        time.sleep(1.0)
        led.value = False
        time.sleep(0.3)
