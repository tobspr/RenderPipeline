

class LightType:

    """ This stores the possible types of light. Python does
    not support enums (yet), so this is a class. """

    NoType = 0
    Point = 1
    Directional = 2
    Spot = 3
    Area = 4
    Ambient = 5