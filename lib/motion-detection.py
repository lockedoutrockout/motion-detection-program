#!/usr/bin/python3

"""
motion-detection.py

Detect motion in video from a live feed or from a file
"""

import os
import sys
import getopt
import configparser
import logging
import imutils
import cv2
from datatypes import Signaller, SignalMonitor

class VideoFeed(object):
    """ Represents an individual video feed
    """
    def __init__(self, config, signaller, debug=False):
        self.debug = debug
        self.config = config
        self.signaller = signaller
        self.signal_monitor = SignalMonitor(self.signaller)
        self.id_no = self.signal_monitor.id_no
        self.logger = logging.getLogger()
        self.process = False

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
        while True:
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
        cv2.destroyAllWindows()
        return None

# Begin execution
if __name__ == "__main__":
	# Process command line arguments
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hdc:W:R:F:", ("help", "debug", "config=", "webcam=", "rtsp=", "file="))
	except getopt.GetoptError as err_msg:
		raise Exception(err_msg)

	# Defaults
	debugging = False
	config_file = "config/motion-detection.cfg"
	webcam_index = None # For webcam source
	rtsp_url = None # For RTSP stream source
	filepath = None # For video file source

	for opt, arg in opts:
		if opt in ("-h", "--help"):
			# Display help message and exit
			print("Bebop's Motion Detection Program (v0.1)")
			print("")
			print("USAGE:")
			print("\t{} [-h] [-d] [-c CONFIG] [-W WEBCAM_INDEX] [-R RTSP_URL] [-F FILEPATH]".format(sys.argv[0]))
			print("")
			print("A program for detecting motion in video from a variety of sources by monitoring the changes in the color value of the ")
			print("pixels in each video frame. Video can be sourced from an attached webcam or builtin camera, an RTSP video stream from a ")
			print("remote device, like an IP camera, or from a static video file.")
			print("")
			print("REQUIRED ARGUMENTS:")
			print("\t-W, --webcam WEBCAM_INDEX\tSource video from the webcam. WEBCAM_INDEX is 0 unless more than one webcam installed")
			print("\t-R, --rtsp RTSP_URL\tSource video from an RTSP stream, such as from a security camera. RTSP_URL points to the URL of the video stream")
			print("\t-F, --file FILEPATH\tSource video from a video file of a supported format. FILEPATH represents the path the the video file")
			print("")
			print("OPTIONAL ARGUMENTS:")
			print("\t-h, --help\tDisplay help message and exit")
			print("\t-d, --debug\tEnable debugging messages")
			print("\t-c, --config CONFIG\tSpecify an alternate configuration file")
			print("")
			print("CONTROLS:")
			print("\tVideo processing and playback can be controlled with the following keys:")
			print("\t\tp\tPauses motion detection processing and video playback")
			print("\t\tq\tQuit the program")
			exit(0)

		elif opt in ("-d", "--debug"):
			# Enable debugging messages
			debugging = True

		elif opt in ("-c", "--config"):
			# Specify an alternate configuration file
			if os.path.isfile(arg) == True:
				config_file = arg
			else:
				raise Exception("Specified configuration file not found!")

		elif opt in ("-W", "--webcam"):
			# Set video source to a webcam
			webcam_index = int(arg)

		elif opt in ("-R", "--rtsp"):
			# Set video source to an RTSP feed
			if "rtsp://" not in arg:
				raise Exception("Invalid RTSP URL provided! The URL to the RTSP must begin with 'RTSP://', please check the URL and try again!")
			rtsp_url = arg

		elif opt in ("-F", "--file"):
			# Set video source to a file
			if "~" in arg:
				arg = os.path.expanduser(arg)
			if os.path.isfile(arg) == True:
				filepath = arg
			else:
				raise Exception("Specified video file not found! Please check the filepath and try again!")

	# Ensure a video source was provided...
	if webcam_index == None and rtsp_url == None and filepath == None:
		raise Exception("No video source provided! Please provide a webcam, RTSP stream, or video file as a source to detect motion from! See -h or --help for usage info!")

	# Banner message
	print("Bebop's Motion Detection Program (v0.1)")
	print("By Brandon Hammond <newdaynewburner@gmail.com>")
	print("")
	print("<------------------------------>")

	# ...But also make sure only one video source was provided
	if webcam_index is not None:
		if rtsp_url is not None or filepath is not None:
			raise Exception("Too many video sources provided! Each video source intended for processing must be handled by a different instance of this script! See -h or --help for usage info!")
		print("[*] Using webcam as video source...")
		print("[*] Index of source camera: {}".format(webcam_index))
		video_source = ("webcam", webcam_index)

	elif rtsp_url is not None:
		if webcam_index is not None or filepath is not None:
			raise Exception("Too many video sources provided! Each video source intended for processing must be handled by a different instance of this script! See -h or --help for usage info!")
		print("[*] Using RTSP stream as video source...")
		print("[*] RTSP stream URL: {}".format(rtsp_url))
		video_source = ("rtsp", rtsp_url)

	elif filepath is not None:
		if webcam_index is not None or rtsp_url is not None:
			raise Exception("Too many video sources provided! Each video source intended for processing must be handled by a different instance of this script! See -h or --help for usage info!")
		print("[*] Using file as video source...")
		print("[*] Path to video file: {}".format(filepath))
		video_source = ("file", filepath)

	# Read configuration file
	print("[*] Reading configuration file data...")
	config = configparser.ConfigParser()
	config.read(config_file)

	# Call main()
	print("[*] Running motion detection algorithm on selected video source now")
	print("")
	print("<------------------------------>")
	main(debugging, config, video_source)
