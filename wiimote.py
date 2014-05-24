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

class WiiMote(object):

    # instance methods
    def __init__(self, btaddr):
        self.btaddr = btaddr
        self.model = "Nintendo RVL-CNT-01"
        self.connected = False
        self._leds = [False, False, False, False]
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
            raise IndexError("List length needs to be exactly %d!" % len(self._leds))
        else:
            self._leds = led_list
            led_byte = 0x00
            for val, state in zip([0x10, 0x20, 0x40, 0x80], led_list):
                if state:
                    led_byte += val
            self._send(RPT_LED, led_byte)

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

RPT_LED = 0x011
