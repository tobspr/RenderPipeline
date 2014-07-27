from panda3d.core import *
img = PNMImage(1, 1)
for faceIndex in xrange(6):
    img.setXel(0, 0, float(faceIndex) / 5.0)
    img.write(str(faceIndex) + ".png")
