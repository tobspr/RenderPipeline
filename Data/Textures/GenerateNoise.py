from panda3d.core import *
from random import random

noise_size = 4

dest = PNMImage(noise_size, noise_size, 3, 2**16 - 1)

for x in xrange(noise_size):
    for y in xrange(noise_size):
        dest.setXel(x, y, random(), random(), random())

dest.write("noise" + str(noise_size) + "x" + str(noise_size) + ".png")