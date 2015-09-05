
""" This module contains generic utility functions """

import hashlib

def rgbFromString(text, minBrightness=0.2):
    """ Creates a rgb color from a given string """
    ohash = hashlib.md5(text).hexdigest()
    r, g, b = int(ohash[0:2],16), int(ohash[2:4],16), int(ohash[4:6],16) 
    negInf = 1.0 - minBrightness
    return minBrightness + r/255.0 * negInf, minBrightness + g/255.0 * negInf, minBrightness + b/255.0 * negInf