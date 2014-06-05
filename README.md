wiimote.py
==========

Wiimote wrapper in pure Python

Usage:

~~~~
import wiimote
btaddr = wiimote.find()[0]
wm = wiimote.connect(btaddr)
wm.leds[3] = True
wm.rumble()
print wm.accelerometer, wm.ir 
wm.buttons.register_callback(print)
~~~~


wiimote_node.py contains a Wiimote node for PyQtGraph:

~~~~
python wiimote_node.py # runs demo
~~~~
