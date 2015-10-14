
""" This module contains generic utility functions """

import hashlib


def rgb_from_string(text, min_brightness=0.4):
    """ Creates a rgb color from a given string """
    ohash = hashlib.md5(text.encode("ascii")).hexdigest()
    r, g, b = int(ohash[0:2], 16), int(ohash[4:6], 16), int(ohash[10:12], 16)
    # Red doesn't look that good, so scale it down
    r *= 0.92
    neg_inf = 1.0 - min_brightness
    return (min_brightness + r / 255.0 * neg_inf,
            min_brightness + g / 255.0 * neg_inf,
            min_brightness + b / 255.0 * neg_inf)
