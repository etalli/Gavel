"""
Gavel – Vibration motor test script

Cycles through the three buzz patterns used in production:
  1. Permission request  — 2 pulses
  2. Button press        — 1 pulse
  3. Error notification  — 3 rapid pulses

Copy this file to the CIRCUITPY drive as code.py to run the test.
Restore the original code.py when done.
"""

import board
import digitalio
import time

motor = digitalio.DigitalInOut(board.GP5)
motor.direction = digitalio.Direction.OUTPUT
motor.value = False

def buzz(times=1, on_ms=60, off_ms=60):
    for _ in range(times):
        motor.value = True
        time.sleep(on_ms / 1000)
        motor.value = False
        time.sleep(off_ms / 1000)

PATTERNS = [
    ("permission request  (2 pulses)",   dict(times=2, on_ms=60, off_ms=60)),
    ("button press        (1 pulse) ",   dict(times=1, on_ms=60)),
    ("error notification  (3 pulses)",   dict(times=3, on_ms=60, off_ms=60)),
]

print("Motor test starting — GP5")
print()

while True:
    for label, kwargs in PATTERNS:
        print("buzzing:", label)
        buzz(**kwargs)
        time.sleep(1.5)
