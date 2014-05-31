#!/usr/bin/env python
# coding: utf-8

# WiiMote wrapper in pure Python
#
# Copyright (c) 2014 Raphael Wimmer <raphael.wimmer@ur.de>
#
# using code from gtkwhiteboard, http://stepd.org/gtkwhiteboard/
# Copyright (c) 2008 Stephane Duchesneau,
# which was modified by Pere Negre and Pietro Pilolli to work with the new WiiMote Plus:
# https://raw.githubusercontent.com/pnegre/python-whiteboard/master/stuff/linuxWiimoteLib.py
#
# LICENSE:         MIT (X11) License:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import bluetooth
import threading
import time

VERSION = (0,1,0)
DEBUG = False

def find():
    """
    Uses Bluetooth SDP to find available Wiimotes. 
    Returns a list of (bt_addr, device_name) tuples.
    Only supported Wiimote devices are returned.
    """
    devices = bluetooth.find_service()
    wiimotes = []
    for device in devices:
        if device["name"] in KNOWN_DEVICES:
            wiimotes.append((device["host"], device["name"]))
    return wiimotes

def connect(btaddr, model=None):
    """
    Establishes a connection to the Wiimote at *btaddr* and returns a Wiimote
    object. If no *model* is specified, the model is determined automatically.
    """
    if model == None:
        model = bluetooth.lookup_name(btaddr)
    if model in KNOWN_DEVICES:
        return WiiMote(btaddr, model)
    else:
        raise Exception("Wiimote model '%s' unknown!" % (model))

def _val_to_byte_list(number, num_bytes, big_endian=True):
    if number > (2**(8*num_bytes))-1:
        raise ValueError("Unsigned integer %d does not fit into %d bytes!" % (number, num_bytes))
    byte_list = []
    for b in range(num_bytes):
        val = (number >> (8*b)) & 0xff
        if big_endian:
            byte_list.insert(0, val)
        else:
            byte_list.append(val)
    return byte_list

def _flatten(list_of_lists):
    out = []
    for item in list_of_lists:
        if type(item) is int:
            out.append(item)
        elif type(item) is list:
            out += _flatten(item)
    return out


def _debug(msg):
    if DEBUG:
        print("DEBUG: " + str(msg))

class Accelerometer(object):
   
    SUPPORTED_REPORTS = [0x31, 0x33]

    def __init__(self, wiimote):
        self._state = [0.0, 0.0, 0.0]
        self._com = wiimote._com

    def __len__(self):
        return len(self._state)

    def __repr__(self):
        return repr(self._state)

    def __getitem__(self, axis):
        if 0 <= axis <= 2:
            return self._state[axis]
        else:
            raise IndexError("list index out of range")
    
    def handle_report(self, report):
        if report[0] in [0x3e, 0x3f]: # interleaved modes
            raise NotImplementedError("Data reporting mode 0x3e/0x3f not supported")
        x_msb, y_msb, z_msb = report[3:6]
        x = (x_msb << 2) + ((report[1] & 0b01100000) >> 5)
        y = (y_msb << 2) + ((report[2] & 0b00100000) >> 4)
        z = (z_msb << 2) + ((report[2] & 0b01000000) >> 5)
        self._state = [x, y, z]
                    
    def _register_callback(self, btn, func):
        pass # todo

    

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

    def __init__(self, wiimote):
        self._wiimote = wiimote
        self._com = wiimote._com
        self._state = {}
        for button in Buttons.BUTTONS.keys():
            self._state[button] = False

    def __len__(self):
        return len(self._state)

    def __repr__(self):
        return repr(self._state)

    def __getitem__(self, btn):
        if self._state.has_key(btn):
            return self._state[btn]
        else:
            raise KeyError(str(btn))

    def handle_report(self, report):
        btn_bytes = (report[1] << 8) + report[2]
        new_state = {}
        for btn, mask in Buttons.BUTTONS.items():
            new_state[btn] = bool(mask & btn_bytes)
        diff = self._update_state(new_state)

    def _update_state(self, new_state):
        diff = []
        for btn, state in new_state.items():
            if self._state[btn] != state:
                diff.append((btn, state))
                self._state[btn] = state
        return diff
                    
    def _register_callback(self, btn, func):
        pass # todo

class LEDs(object):

    def __init__(self, wiimote):
        self._state = [False, False, False, False]
        self._com = wiimote._com

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
        self._com.set_led_state(self._state)

class Rumbler(object):

    def __init__(self, wiimote):
        self._state = False
        self.wiimote = wiimote

    def set_rumble(self, state):
        self._state = state
        self.wiimote._com.set_rumble(state)

    def rumble(self, length=0.5):
        t = threading.Timer(length, self.set_rumble, [False])
        t.start()
        self.set_rumble(True)

class IRCam(object):

    MODE_BASIC = 1
    MODE_EXTENDED = 3
    MODE_FULL = 5
    
    SUPPORTED_REPORTS = [0x33, 0x36,0x37,0x3e,0x3f]

    def __init__(self, wiimote):
        self.wiimote = wiimote
        self._state = []
        self._mode = IRCam.MODE_BASIC

    def get_state(self):
        return self._state

    def set_mode(self):
        pass


class Memory(object):

    RPT_READ = 0x17
    RPT_WRITE = 0x16
    
    SUPPORTED_REPORTS = [0x21]

    def __init__(self, wiimote):
        self.wiimote = wiimote
        self._com = wiimote._com
        self._request_in_progress = False
        self._bytes_requested = 0
        self._reply_buffer = []


    def write(self, address, data, eeprom=False):
        raise NotImplementedError("not implemented yet")

    def read(self, address, amount, eeprom=False):
        if self._request_in_progress:
            raise RuntimeError("Memory read already in progress.")
        self._bytes_remaining = amount
        address_bytes = _val_to_byte_list(address, 3, big_endian=True)
        amount_bytes = _val_to_byte_list(amount, 2, big_endian=True)
        control_or_eeprom = 0x00 if eeprom else 0x02
        self._request_in_progress = True
        self._reply_buffer = []
        self._com._send(Memory.RPT_READ, control_or_eeprom, address_bytes, amount_bytes) 
        # now wait until handle() has filled our reply buffer
        while self._request_in_progress:
            time.sleep(0.01)
        return self._reply_buffer

    def handle_report(self, report):
        if report[0] not in Memory.SUPPORTED_REPORTS: # interleaved modes
            raise NotImplementedError("can not handle this report")
        error = (report[3] & 0x0f) 
        if error != 0:
            raise RuntimeError("Error condition %x received during memory read!" % error)
        num_bytes_received = ((report[3] >> 4) & 0x0f) + 1
        data_bytes = report[6:][:num_bytes_received]
        self._reply_buffer += data_bytes
        self._bytes_remaining -= num_bytes_received
        if self._bytes_remaining < 0:
            raise RuntimeError("Memory read received more data than requested!")
        elif self._bytes_remaining == 0:
            self._request_in_progress = False


class CommunicationHandler(threading.Thread):
    
    MODE_DEFAULT = 0x30
    MODE_ACC     = 0x31

    RPT_STATUS_REQ = 0x15

    def __init__(self, wiimote):
        threading.Thread.__init__(self)
        self.daemon = True
        self.rumble = False # rumble always 
        self.wiimote = wiimote
        self.btaddr = wiimote.btaddr
        self.model = wiimote.model
        self.reporting_mode = self.MODE_DEFAULT
        self._controlsocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        self._controlsocket.connect((self.btaddr, 17))
        self._datasocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        self._datasocket.connect((self.btaddr, 19))
        if self.model == 'Nintendo RVL-CNT-01':
            self._sendsocket = self._controlsocket
            self._CMD_SET_REPORT = 0x52
        elif self.model == 'Nintendo RVL-CNT-01-TR':
            self._sendsocket = self._datasocket
            self._CMD_SET_REPORT = 0xa2
        else:
            raise Exception("unknown model")
        try:
            self._datasocket.settimeout(1)
        except NotImplementedError:
            print "socket timeout not implemented with this bluetooth module"
        self.set_report_mode(self.MODE_ACC)
    
    def _send(self, *bytes_to_send):
        _debug("sending " + str(bytes_to_send))
        data_str = chr(self._CMD_SET_REPORT)
        bytes_to_send = _flatten(bytes_to_send)
        bytes_to_send[1] &= int(self.rumble)
        for b in bytes_to_send:
            data_str += chr(b)
        self._sendsocket.send(data_str)

    def run(self):
        self.running = True
        while self.running:
            try:
                data = map(ord,self._datasocket.recv(32))
            except bluetooth.BluetoothError:
                continue
            self._handle(data)
        self._dispose()

    def _dispose(self):
        self._datasocket.close()
        self._controlsocket.close()
        self.running = False

    def set_report_mode(self, mode):
        self.reporting_mode = mode
        self._send(0x12, 0x00, mode)

    def _handle(self, bytes_read):
        _debug(bytes_read)
        #assert(bytes_read[0] == self._CMD_SET_REPORT + 1)
        rpt_type = bytes_read[1]
        # all reports include button data
        self.wiimote.buttons.handle_report(bytes_read[1:])
        if rpt_type in Accelerometer.SUPPORTED_REPORTS:
            self.wiimote.accelerometer.handle_report(bytes_read[1:])
        if rpt_type in Memory.SUPPORTED_REPORTS:
            self.wiimote.memory.handle_report(bytes_read[1:])

    def set_led_state(self, led_state):
        RPT_LED = 0x11
        led_byte = 0x00
        for val, state in zip([0x10, 0x20, 0x40, 0x80], led_state):
            if state:
               led_byte += val
        self._send(RPT_LED, led_byte)

    def set_rumble(self, state):
        self.rumble = state
        # send any report to toggle rumble bit
        self._send(self.RPT_STATUS_REQ, int(state))


class WiiMote(object):

    # instance methods
    def __init__(self, btaddr, model):
        self.btaddr = btaddr
        self.model = model
        self.connected = False
        self._com = CommunicationHandler(self)
        self._leds = LEDs(self)
        self.accelerometer = Accelerometer(self)
        self.buttons = Buttons(self)
        self.rumbler = Rumbler(self)
        self.memory = Memory(self)
        self._com.start()
       
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

    def rumble(self, length=0.5):
        self.rumbler.rumble(length)

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

