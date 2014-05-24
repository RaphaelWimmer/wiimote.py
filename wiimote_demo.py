#!/usr/bin/env python

import wiimote

raw_input("Press the 'sync' button on the back of your Wiimote Plus\
           or buttons (1) and (2) on your classic Wiimote. \
           Press <return> once the Wiimote's LEDs start blinking.")

addr, name = wiimote.find()[0]
wm = wiimote.connect(addr, name)
wm.leds[0] = True

