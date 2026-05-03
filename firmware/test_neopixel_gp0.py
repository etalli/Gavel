"""
Gavel – External NeoPixel test script (GP0)

Cycles through colors to verify wiring:
  red → green → blue → white → off → repeat

Copy this file to the CIRCUITPY drive as code.py to run the test.
Restore the original code.py when done.
"""

import board
import neopixel
import time

np = neopixel.NeoPixel(board.GP0, 1, brightness=0.3, auto_write=True)

COLORS = [
    ((255,   0,   0), "red"),
    ((  0, 255,   0), "green"),
    ((  0,   0, 255), "blue"),
    ((255, 255, 255), "white"),
    ((  0,   0,   0), "off"),
]

print("NeoPixel test starting — GP0")
print()

while True:
    for color, label in COLORS:
        print("color:", label)
        np[0] = color
        time.sleep(1.0)
