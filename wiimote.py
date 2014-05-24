#!/usr/bin/env python
# coding: utf-8

import bluetooth


def find():
    devices = bluetooth.find_service()
    wiimotes = []
    for device in devices:
        if device["name"] in KNOWN_DEVICES.keys():
            wiimotes.append((device["host"], device["name"]))
    return wiimotes
        
def get_model(btaddr):
    devices = bluetooth.find_service()
    for device in devices:
        if device["host"] == btaddr:
            return device["name"]
    return None
    

def connect(btaddr, model=None):
    wiimote = None
    if model == None:
        model = get_model(btaddr)
    if model in KNOWN_DEVICES.keys():
        return KNOWN_DEVICES[model](btaddr)
    else:
        raise Exception("Wiimote model '%s' unknown!" % (model))

class Buttons(object):
    
    def __init__(self, device):
        self._device = device
        self._state = {}
        for button in Buttons.BUTTONS:
            self._state[button] = False

    def __len__(self):
        return len(self._state)

    def __repr__(self):
        return repr(self._state)

    def __getitem__(self, btn):
        if btn in Buttons.BUTTONS:
            return self._state[btn]
        else:
            raise KeyError(str(btn))

    def _update(self, report):
        pass

    def _register_callback(self, btn, func):
        pass # todo

class LEDs(object):

    def __init__(self, device):
        self._state = [False, False, False, False]
        self._device = device

    def __len__(self):
        return len(self._state)

    def __repr__(self):
        return repr(self._state)

    def __getitem__(self, led_no):
        if 0 <= led_no <= 3:
            return self._state[led_no]
        else:
            raise IndexError("list index out of range")

    def __setitem__(self, led_no, val):
        new_led_state = self._state
        if 0 <= led_no <= 3:
            new_led_state[led_no] = True if val else False
            self.set_leds(new_led_state)
        else:
            raise IndexError("list index out of range")

    def set_leds(self, led_list):
        for led_no, val in enumerate(led_list):
            self._state[led_no] = True if val else False
        self.send_led_state()

    def send_led_state(self):
        RPT_LED = 0x11
        led_byte = 0x00
        for val, state in zip([0x10, 0x20, 0x40, 0x80], self._state):
            if state:
               led_byte += val
        self._device._send(RPT_LED, led_byte)


class WiiMote(object):

    # instance methods
    def __init__(self, btaddr):
        self.btaddr = btaddr
        self.model = "Nintendo RVL-CNT-01"
        self.connected = False
        self._leds = LEDs(self)
        self._socket = None
        
        self.connect()
       
    def connect(self):
        self._controlsocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        self._controlsocket.connect((self.btaddr,17))
        self._datasocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        self._datasocket.connect((self.btaddr,19))
        self._socket = self._controlsocket
        self._CMD_SET_REPORT = 0x52
        try:
            self._datasocket.settimeout(1)
        except NotImplementedError:
            print "socket timeout not implemented with this bluetooth module"
    
    def _disconnect(self):
        pass

    def _get_capabilities(self):
        return None

    def _get_state(self):
        return None

    def _set_state(self, state):
        pass

    def _reset(self):
        pass

    ### LEDs ###

    def get_leds(self):
        return self._leds

    def set_leds(self, led_list):
        if len(led_list) != len(self._leds):
            raise IndexError("list length needs to be exactly %d!" % len(self._leds))
        else:
            self._leds.set_leds(led_list)

    def _send(self, *bytes_to_send):
        print("sending " + str(bytes_to_send))
        data_str = chr(self._CMD_SET_REPORT)
        for b in bytes_to_send:
            data_str += chr(b)
        self._socket.send(data_str)

    leds = property(get_leds, set_leds)

    #rumble = property(get_rumble, set_rumble)


class WiiMotePlus(WiiMote):
    
    def connect(self):
        super(WiiMotePlus, self).connect()
        self._CMD_SET_REPORT = 0xa2
        self._socket = self._datasocket

KNOWN_DEVICES = {'Nintendo RVL-CNT-01': WiiMote,
                 'Nintendo RVL-CNT-01-TR': WiiMotePlus,
                 }

