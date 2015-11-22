from __future__ import division, print_function

import math
from panda3d.core import PNMImage

lut_size = 64
lut_cols = 8
lut_rows = (lut_size + lut_cols - 1) // lut_cols

img = PNMImage(lut_size * lut_cols, lut_size * lut_rows, 3, 2**16 - 1)

def to_linear(v):
    return float(v) / float(lut_size-1)

def to_linear_inv(v):
    return 1 - to_linear(v)

for r in range(lut_size):
    for g in range(lut_size):
        for b in range(lut_size):
            slice_offset_x = (b % lut_cols) * lut_size
            slice_offset_y = (b // lut_cols) * lut_size
            img.set_xel(r + slice_offset_x, g + slice_offset_y, 
                to_linear(r), to_linear_inv(g), to_linear(b))

img.write("DefaultLUT.png")
