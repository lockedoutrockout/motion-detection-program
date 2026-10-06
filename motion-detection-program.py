#!/usr/bin/env python3

"""
motion-detection-program.py

Intelligent security camera system
"""

import os
import sys
import subprocess
import threading
import logging
import configparser
import getopt
from lib import videofeeds, datatypes, exceptions

def main(debug, config, logger, sources):
    """ Main function. Contains core program logic
    """
    signaller = datatypes.Signaller(debug=debug, logger=logger)
    video_feeds = []
    logger.info(f"Establishing video feed connections...")
    for video_source in sources:
        logger.info(f"\t...Loading video feed from {video_source[0]} source (reflink: {video_source[1]})...")
        video_feed = videofeeds.VideoFeed(
            video_source,
            signaller,
            debug=debug,
            config=config,
            logger=logger
        )
        video_feeds.append(video_feed)
        logger.info(f"\t...Done! Video feed from {video_source[0]} source (reflink: {video_source[1]}) loaded and assigned ID number: {video_feed.id_no}...")
    logger.info(f"...Done! All video feed connections have been established!")
    input("Press [ENTER] to continue...")
    signaller.signal("START")
    signaller.signal("ENABLEDISPLAY")
    input("Press [ENTER] to continue...")
    signaller.signal("DISABLEDISPLAY")
    signaller.signal("STOP")
    signaller.signal("SHUTDOWN")

# Begin execution
if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hdc:",
            [
                "help",
                "debug",
                "config="
            ]
        )
    except getopt.GetoptError as err_msg:
        raise err_msg
        
    debug = False
    config_file = "config/motion-detection-program.ini"
    sources = []
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(f"USAGE:")
            print(f"\t{sys.argv[0]} [-h] [-d] [-c CONFIG_FILE] SOURCES")
            print(f"")
            print(f"OPTIONS:")
            print(f"\t-h, --help\t\tDisplay the help message and exit")
            print(f"\t-d, --debug\t\tRun in debugging mode")
            print(f"\t-c, --config CONFIG_FILE\tSpecify the configuration file to use")
            print(f"")
            print(f"ARGUMENTS:")
            print(f"\tSOURCES\t\tOne or more video sources. Formatted as TYPE+REFLINK")
            sys.exit(0)
        elif opt in ("-d", "--debug"):
            debug = True
        elif opt in ("-c", "--config"):
            if "~" in arg:
                arg = os.path.expanduser(arg)
            if not os.path.isfile(arg):
                raise FileNotFoundError
            config_file = arg
            
    if len(args) < 1:
        raise Exception
    for arg in args:
        if "+" not in arg:
            raise ValueError
        stype, sref = arg.split("+")
        if stype not in datatypes.SOURCETYPES:
            raise ValueError
        sources.append((stype, sref))
        
    config = configparser.ConfigParser()
    config.read(config_file)
    
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger()
        
    main(debug, config, logger, sources)
            
    
