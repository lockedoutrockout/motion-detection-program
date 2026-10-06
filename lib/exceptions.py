"""
lib/exceptions.py

Custom exceptions
"""

class SignalError(Exception):
    """ Parent class of all signal related exceptions
    """
    def __init__(self, msg):
        super().__init__(msg)
