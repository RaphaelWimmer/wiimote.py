#!/usr/bin/env python
# coding: utf-8

import bluetooth


def find():
    devices = bluetooth.find_service()
    wiimotes = []
    for device in devices:
        if device["name"] in KNOWN_DEVICES:
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
    if model in KNOWN_DEVICES:
        return WiiMote(btaddr, model)
    else:
        raise Exception("Wiimote model '%s' unknown!" % (model))

class Buttons(object):
    
    BUTTONS = {'A': 0x0008,
               'B': 0x0004,
               'Down' : 0x0400,
               'Home': 0x0080,
               'Left': 0x0100,
               'Minus': 0x0010,
               'One': 0x0002,
               'Plus': 0x1000,
               'Right': 0x0200,
               'Two': 0x0001,
               'Up': 0x0800,
    }

    def __init__(self, device):
        self._device = device
        self._state = {}
        for button in Buttons.BUTTONS.keys():
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

    def __init__(self, com_mgr):
        self._state = [False, False, False, False]
        self._com = com_mgr

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
        self._com.write_led_state(self._state)

    def send_led_state(self):
        RPT_LED = 0x11
        led_byte = 0x00
        for val, state in zip([0x10, 0x20, 0x40, 0x80], self._state):
            if state:
               led_byte += val
        self._device._send(RPT_LED, led_byte)

class CommunicationHandler(object):

    def __init__(self, btaddr, model):
        self.rumble = False # rumble always 
        self.btaddr = btaddr
        self.model = model
        self._controlsocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        self._controlsocket.connect((self.btaddr, 17))
        self._datasocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        self._datasocket.connect((self.btaddr, 19))
        if self.model == 'Nintendo RVL-CNT-01':
            self._socket = self._controlsocket
            self._CMD_SET_REPORT = 0x52
        elif self.model == 'Nintendo RVL-CNT-01-TR':
            self._socket = self._datasocket
            self._CMD_SET_REPORT = 0xa2
        else:
            raise Exception("unknown model")
        try:
            self._datasocket.settimeout(1)
        except NotImplementedError:
            print "socket timeout not implemented with this bluetooth module"
    
    def _send(self, *bytes_to_send):
        print("sending " + str(bytes_to_send))
        data_str = chr(self._CMD_SET_REPORT)
        for b in bytes_to_send:
            data_str += chr(b)
        self._socket.send(data_str)

    def write_led_state(self, led_state):
        RPT_LED = 0x11
        led_byte = 0x00
        for val, state in zip([0x10, 0x20, 0x40, 0x80], led_state):
            if state:
               led_byte += val
        self._send(RPT_LED, led_byte)

class WiiMote(object):

    # instance methods
    def __init__(self, btaddr, model):
        self.btaddr = btaddr
        self.model = model
        self.connected = False
        self.connect()
        self._leds = LEDs(self._com)
       
    def connect(self):
        self._com = CommunicationHandler(self.btaddr, self.model)
        #self.connected = self._com.connected()
    
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

    leds = property(get_leds, set_leds)

    #rumble = property(get_rumble, set_rumble)

KNOWN_DEVICES = ['Nintendo RVL-CNT-01', 'Nintendo RVL-CNT-01-TR']

