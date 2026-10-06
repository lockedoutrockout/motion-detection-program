"""
lib/datatypes.py

Custom datatype definitions
"""

import os
import sys
import time
import threading

SOURCETYPES = ["webcam", "rtsp", "videofile"]
SIGTYPES = ["START", "STOP", "ENABLEDISPLAY", "DISABLEDISPLAY", "SHUTDOWN"]

class Signal(object):
    """ Represents a signal
    """
    def __init__(self, stype, smsg="", sscope=()):
        if stype not in SIGTYPES:
            raise Exception(f"Invalid signal type: {stype}")
        self.stype = stype
        self.smsg = smsg
        self.sscope = sscope
        self.sts = time.time_ns()
        

class Signaller(object):
    """ Used to send signals to video feed controllers
    """
    def __init__(self):
        self.listeners = {}
        self.signals = []
        
    def register_listener(self, monitor):
        """ Register a new listener
        """
        id_no = len(self.listeners.keys()) + 1
        self.listeners[id_no] = monitor
        return id_no
        
    def signal(self, stype, smsg="", sscope=()):
        """ Send a signal
        """
        signal = Signal(
            stype,
            smsg=smsg,
            sscope=sscope
        )
        self.signals.append(signal)
        for listener in self.listeners.values():
            if listener.id_no in signal.sscope or len(signal.sscope) == 0:
                listener.new_incoming(signal)
        
        
class SignalMonitor(object):
    """ Used to monitor for signals
    """
    def __init__(self, parent, signaller):
        self.parent = parent
        self.signaller = signaller
        self.id_no = self.signaller.register_listener(self)
        self.signals = []
        
    def new_incoming(self, signal):
        """ Process new signals
        """
        def _thread(parent, signal):
            """ Signal handler thread target
            """
            if signal.stype == "START":
                setattr(parent, "_do_processing", True)
            elif signal.stype == "STOP":
                setattr(parent, "_do_processing", False)
            elif signal.stype == "ENABLEDISPLAY":
                setattr(parent, "_show_feed", True)
            elif signal.stype == "DISABLEDISPLAY":
                setattr(parent, "_show_feed", False)
            elif signal.stype == "SHUTDOWN":
                setattr(parent, "_shutdown", True)
            
        self.signals.append(signal)
        threading.Thread(
            target=_thread,
            args=(self.parent, signal),
            daemon=True
        ).start()
        return None
        
