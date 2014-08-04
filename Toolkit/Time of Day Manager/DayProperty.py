
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


class PropertyTypeInt(PropertyType):

    """ Int property. See PropertyType """


class PropertyTypeFloat(PropertyType):

    """ Float property. See PropertyType """


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

    def setValue(self, index, val):
        self.values[index] = round(val, 5)
