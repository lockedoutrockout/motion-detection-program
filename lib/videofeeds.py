#!/usr/bin/python3

"""
motion-detection.py

Detect motion in video from a live feed or from a file
"""

import os
import sys
import threading
import getopt
import configparser
import logging
import imutils
import cv2
from . import datatypes

class VideoFeed(object):
    """ Represents an individual video feed
    """
    def __init__(self, video_source, signaller, debug=False, config=None, logger=None):
        def main():
            """ Main logic for video feed
            """
            while not self._shutdown:
                self._processing_thread = threading.Thread(target=self.process, daemon=True)
                self._processing_thread.start()
                self._processing_thread.join()
            
        
        self.debug = debug
        self.config = config
        self.logger = logger
        
        self.video_source = video_source
        self.signaller = signaller
        self.signal_monitor = datatypes.SignalMonitor(self, self.signaller)
        self.id_no = self.signal_monitor.id_no
        self._do_processing = False
        self._show_feed = False
        self._shutdown = False
        
        threading.Thread(target=main, daemon=True).start()

    def process(self):
        """ Main video processing loop
        """

        # Unpack various values related to the motion detection algorithm from the configuration data
        sensitivity = int(self.config["DEFAULT"]["sensitivity"])
        reference_frame_reset_interval = int(self.config["DEFAULT"]["reference_frame_reset_interval"])

        # Open the video source and go through it frame by frame
        vs = cv2.VideoCapture(self.video_source[1])
        frame_number = 0
        frames_with_motion = [] # [(frame_number, original_frame)]
        reference_frame = None
        reference_frames_taken = 0
        c = 0
        while self._do_processing:
            _, frame = vs.read()

            # If the frame is empty, video has ended and this loop should be broken
            if frame is None:
                break
            else:
                frame_number = frame_number + 1
                c = c + 1
                original_frame = frame

            # Resize, gray, and blur the frame for easier processing
            frame = imutils.resize(frame, width=500)
            pframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            pframe = cv2.GaussianBlur(pframe, (21, 21), 0)

            # Take the initial reference frame, or set a new one if at the interval
            if reference_frame is None or c == reference_frame_reset_interval:
                reference_frame = pframe
                reference_frames_taken = reference_frames_taken + 1
                if c == reference_frame_reset_interval:
                    c = 0

            # Calculate the difference between the current frame and the reference
            delta = cv2.absdiff(reference_frame, pframe)
            threshold = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]

            # Find contours on the threshold image
            threshold = cv2.dilate(threshold, None, iterations=2)
            contours = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = imutils.grab_contours(contours)

            # Loop through all found contours and check if any breach the motion detection sensitivity threshold
            areas_with_motion = 0
            for contour in contours:
                # Pass by contours that are smaller than the set sensitivity level
                if cv2.contourArea(contour) < sensitivity:
                    continue

                areas_with_motion = areas_with_motion + 1
                frames_with_motion.append((frame_number, original_frame))

                # Draw a box around detected motion
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Log detected motion
            if areas_with_motion > 0:
                self.logger.debug(f"Motion detected in frame {frame_number} in {areas_with_motion} area(s)")
                
            # Display video
            if self._show_feed: 
                cv2.imshow(f"Bebop's Motion Detection Program ({self.video_source[0]} <{self.video_source[1]}>)", frame)
                # DEBUGGING
                #if self.debug:
                #    cv2.imshow("[DEBUG] Bebop's Motion Detection Program - REFERENCE FRAME", reference_frame)
                #    cv2.imshow("[DEBUG] Bebop's Motion Detection Program - IMAGE THRESHOLD", threshold)
                #    cv2.imshow("[DEBUG] Bebop's Motion Detection Program - FRAME DELTA", delta)

                # Wait for keypresses
                key = cv2.waitKey(1) & 0xFF
                if key == ord("p"):
                    input("[i] Motion detection processing paused. Press [ENTER] to continue...")
                elif key == ord("q"):
                    break

        # Exit from the function cleanly
        if self._show_feed:
            cv2.destroyAllWindows()
        return None
