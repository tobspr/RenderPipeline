from panda3d.core import *
s = 1
img = PNMImage(s,s)
for faceIndex in xrange(6):
    for x in xrange(s):
        for y in xrange(s):
            img.setXel(x, y, float(faceIndex) / 5.0 )
    img.write(str(faceIndex) + ".png")
