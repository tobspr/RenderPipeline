
""" This module contains generic utility functions """

import hashlib


def rgb_from_string(text, min_brightness=0.6):
    """ Creates a rgb color from a given string """
    ohash = hashlib.md5(text[::-1].encode("ascii")).hexdigest()
    r, g, b = int(ohash[0:2], 16), int(ohash[2:4], 16), int(ohash[4:6], 16)
    neg_inf = 1.0 - min_brightness
    return (min_brightness + r / 255.0 * neg_inf,
            min_brightness + g / 255.0 * neg_inf,
            min_brightness + b / 255.0 * neg_inf)

