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
    def __init__(self, debug=None, logger=None):
        self.debug = debug
        self.logger = logger
        self.listeners = {}
        self.signals = []
        self.logger.debug(f"New Signaller object initialized")

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
        self.logger.debug(f"Signaller object has sent a new Signal. stype={signal.stype}, smsg={signal.smsg}, sscope={signal.sscope}")


class SignalMonitor(object):
    """ Used to monitor for signals
    """
    def __init__(self, parent, signaller):
        self.parent = parent
        self.signaller = signaller
        self.logger = self.parent.logger
        self.id_no = self.signaller.register_listener(self)
        self.signals = []
        self.logger.debug(f"New SignalMonitor object initialized and registered with Signaller. Assigned ID {self.id_no}")

    def new_incoming(self, signal):
        """ Process new signals
        """
        def _thread(signal):
            """ Signal handler thread target
            """
            self.logger.debug(f"SignalMonitor with ID {self.id_no} passed new Signal to it's handler thread. Context of parent pre-processing: _do_processing={parent._do_processing}, _show_feed={parent._show_feed}, _shutdown={parent._shutdown}")
            if signal.stype == "START":
                setattr(self.parent, "_do_processing", True)
            elif signal.stype == "STOP":
                setattr(self.parent, "_do_processing", False)
            elif signal.stype == "ENABLEDISPLAY":
                setattr(self.parent, "_show_feed", True)
            elif signal.stype == "DISABLEDISPLAY":
                setattr(self.parent, "_show_feed", False)
            elif signal.stype == "SHUTDOWN":
                setattr(self.parent, "_shutdown", True)
            self.logger.debug(f"SignalMonitor with ID {self.id_no} processed new Signal with it's handler thread. Context of parent post-processing: _do_processing={parent._do_processing}, _show_feed={parent._show_feed}, _shutdown={parent._shutdown}")

        self.signals.append(signal)
        self.logger.debug(f"SignalMonitor object with ID {self.id_no} received new incoming Signal. stype={signal.stype}, smsg={signal.smsg}, sscope={signal.sscope}")
        threading.Thread(
            target=_thread,
            args=(signal),
            daemon=True
        ).start()
        return None

