
import math
from panda3d.core import NurbsCurve, Vec3


class PropertyType:

    """ Base property type. Types like PropertyTypeFloat are subclasses
    of this. This class is used to store the min/max values of time of day
    properties, and also convert them from/to 0 .. 1 range. """

    def __init__(self, minVal, maxVal):
        """ Constructs a new poperty, setting min and max value """
        self.minVal = minVal
        self.maxVal = maxVal

    def asUniform(self, val):
        """ Converts a value from minVal .. maxVal to 0 .. 1 """
        return (val - self.minVal) / (self.maxVal - self.minVal)

    def fromUniform(self, val):
        """ Converts a value from 0 .. 1 to minVal .. maxVal """
        return val * (self.maxVal - self.minVal) + self.minVal

    def convertString(self, val):
        """ Converts a string to a typed value """
        return val


class PropertyTypeFloat(PropertyType):

    """ Float property. See PropertyType """

    def convertString(self, val):
        return max(self.minVal, min(self.maxVal, float(val)))


class DayProperty:

    """ Stores a time of day property, including name, description, type,
    min/max and default value """

    def __init__(self, name, typeName, minVal, maxVal, defaultVal, description):
        self.name = name
        if typeName == "float":
            self.propType = PropertyTypeFloat(minVal, maxVal)
        else:
            print "Unrecognized Type:", typeName

        self.description = description.strip()
        self.defaultValue = defaultVal
        self.values = [self.defaultValue for i in xrange(8)]
        self.curve = NurbsCurve()
        self.curve.setOrder(3)

    def setValue(self, index, val):
        self.values[index] = round(val, 5)

    def recompute(self):
        """ Recomputes the NURBS Curve for this property """
        self.curve.removeAllCvs()

        # Pad, to make 00:00 match with 24:00
        # Thanks to rdb for finding a bug here
        padIndices = [5, 6, 7, 0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2]

        paddedValues = [self.values[i] for i in padIndices]

        for index, val in enumerate(paddedValues):
            self.curve.appendCv(Vec3(index, val, 0.0))

        self.curve.recompute()

    def getInterpolatedValue(self, pos):
        tmp = Vec3(0)
        self.curve.getPoint(pos * 8.0 + 2.5, tmp)
        return tmp.y

