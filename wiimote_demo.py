#!/usr/bin/env python

import wiimote
import time
import sys

if len(sys.argv) < 3:
    raw_input("Press the 'sync' button on the back of your Wiimote Plus " +
          "or buttons (1) and (2) on your classic Wiimote. " +
          "Press <return> once the Wiimote's LEDs start blinking.")
    addr, name = wiimote.find()[0]
else:
    addr, name = sys.argv[1:3]
print("Connecting to %s (%s)" % (name, addr))
wm = wiimote.connect(addr, name)
patterns = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
while True:
    for p in patterns:
        wm.leds = p
        time.sleep(0.05)

