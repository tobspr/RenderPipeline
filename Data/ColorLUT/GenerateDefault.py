

from panda3d.core import PNMImage, Vec3

lutSize = 32

image = PNMImage(lutSize * lutSize, lutSize, 3, 2**16 - 1)


for r in xrange(lutSize):
    for g in xrange(lutSize):
        for b in xrange(lutSize):
            image.setXel(r + b * lutSize, g, r / float(lutSize), g / float(lutSize), b / float(lutSize))

image.write("Default.png")