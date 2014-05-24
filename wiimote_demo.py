#!/usr/bin/env python

import wiimote
import time

raw_input("Press the 'sync' button on the back of your Wiimote Plus " +
          "or buttons (1) and (2) on your classic Wiimote. " +
          "Press <return> once the Wiimote's LEDs start blinking.")

addr, name = wiimote.find()[0]
wm = wiimote.connect(addr, name)
patterns = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
while True:
    for p in patterns:
        wm.leds = p
        time.sleep(0.1)

