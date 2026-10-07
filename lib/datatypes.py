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
    def __init__(self, feed_state, signaller, logger=None):
        self.logger = logger
        self.feed_state = feed_state
        self.signaller = signaller
        self.id_no = self.signaller.register_listener(self)
        self.signals = []
        self.logger.debug(f"New SignalMonitor object initialized and registered with Signaller. Assigned ID {self.id_no}")

    def new_incoming(self, signal):
        """ Process new signals
        """
        def _thread(signal):
            """ Signal handler thread target
            """
            if signal.stype == "START":
                self.feed_state.do_processing.set()
            elif signal.stype == "STOP":
                self.feed_state.do_processing.clear()
            elif signal.stype == "ENABLEDISPLAY":
                self.feed_state.show_feed.set()
            elif signal.stype == "DISABLEDISPLAY":
                self.feed_state.show_feed.clear()
            elif signal.stype == "SHUTDOWN":
                self.feed_state.shutdown.set()

        self.signals.append(signal)
        self.logger.debug(f"SignalMonitor object with ID {self.id_no} received new incoming Signal. stype={signal.stype}, smsg={signal.smsg}, sscope={signal.sscope}")
        threading.Thread(
            target=_thread,
            args=(signal,),
            daemon=True
        ).start()
        return None

