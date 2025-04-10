from setuptools import setup, find_packages

setup(
	name="motion-detection-program",
	version="0.1",
	url="https://github.com/newdaynewburner/motion-detection-program",
	author="Brandon Hammond",
	author_email="newdaynewburner@gmail.com",
	description="A multi-source video motion detection program with adjustable sensitivity. Capable of detecting motion in video footage sourced from webcams and built-in cameras, RTSP video streams from remote devices, and also from static video files. Written in Python and powered by OpenCV.",
	packages=find_packages(),
	install_requires=["imutils", "cv2"],
)
