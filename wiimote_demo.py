#!/usr/bin/env python

import wiimote
import time
import sys
    
raw_input("Press the 'sync' button on the back of your Wiimote Plus " +
          "or buttons (1) and (2) on your classic Wiimote.\n" +
          "Press <return> once the Wiimote's LEDs start blinking.")

if len(sys.argv) == 1:
    addr, name = wiimote.find()[0]
elif len(sys.argv) == 2:
    addr = sys.argv[1]
    name = None
elif len(sys.argv) == 3:
    addr, name = sys.argv[1:3]
print("Connecting to %s (%s)" % (name, addr))
wm = wiimote.connect(addr, name)

# Demo Time!
patterns = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1],[0,0,1,0],[0,1,0,0],[1,0,0,0]]
for i in range(5):
    for p in patterns:
        wm.leds = p
        time.sleep(0.05)


def print_ir(ir_data):
    if len(ir_data) == 0:
        return
    for ir_obj in ir_data:
        print "%4d %4d %2d     " % (ir_obj["x"],ir_obj["y"],ir_obj["size"]),
    print

wm.ir.register_callback(print_ir)

while True:
    if wm.buttons["A"]:
        wm.leds[1] = True
        wm.rumble(0.1)
        print(wm.accelerometer)
    else:
        wm.leds[1] = False
        pass
    time.sleep(0.05)

