#!/usr/bin/env python

import wiimote

addr, name = wiimote.list()[0]
wm = wiimote.connect(addr, name)
wm.leds[0] = True

