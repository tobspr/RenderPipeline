

class PropertyType:

    def __init__(self, minVal, maxVal):
        self.minVal = minVal
        self.maxVal = maxVal

    def asUniform(self, val):
        return (val-self.minVal) / (self.maxVal - self.minVal)

    def fromUniform(self, val):
        return (val * (self.maxVal - self.minVal)) + self.minVal


class PropertyTypeInt(PropertyType):
    pass


class PropertyTypeFloat(PropertyType):
    pass


class DayProperty:

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
