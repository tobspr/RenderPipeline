
import os

from panda3d.core import Texture, PNMImage, SamplerState
# from direct.stdpy.file import open

from DebugObject import DebugObject

class IESLoader(DebugObject):

    """ This class manages the loading of IES Profiles and combining them into
    a texture so they can be used in a shader """
       

    # All supported IES Profile versions
    IESVersionTable = {
        'IESNA:LM-63-1986': 1986,
        'IESNA:LM-63-1991': 1991,
        'IESNA91':          1991,
        'IESNA:LM-63-1995': 1995,
        'IESNA:LM-63-2002': 2002,
    }

    # Controls the size of the precomputed ies tables. Bigger values mean more
    # precision but also more storage required
    IESTableResolution = 256

    def __init__(self):
        """ Creates a new IES Loader """
        DebugObject.__init__(self, "IESLoader")
        self.debug("Creating IES Loader")
        self.storage = Texture("IESProfiles")
        self.storage.setup2dTextureArray(self.IESTableResolution, 1, 64, Texture.TFloat, Texture.FRgb16)
        self.storage.setMinfilter(SamplerState.FTLinear)
        self.storage.setMagfilter(SamplerState.FTLinear)
        self.storage.setWrapU(SamplerState.WMClamp)
        self.storage.setWrapV(SamplerState.WMClamp)
        self.storage.setWrapW(SamplerState.WMClamp)

        self.profileNames = []

    def getIESProfileStorageTex(self):
        """ Returns the texture array where all ies profiles are stored in """
        return self.storage

    def loadIESProfiles(self, directory):
        """ Loads all ies profiles from a given directory """
        self.debug("Loading IES Profiles from", directory)

        files = os.listdir(directory)

        for entry in files:
            if entry.lower().endswith(".ies"):
                combinedPath = os.path.join(directory, entry)
                self._loadIESProfile(entry.split(".")[0], combinedPath)



    def _storeIESProfile(self, name, lampRadialGradientData, lampGradientData):
        """ Internal method to convert the array of data into a texture to load
        into the texture array """

        def interpolateValue(dataset, percentageVal):
            """ Interpolates over an array, accepting float values from 0.0 to 1.0 """
            percentageValClamped = max(0.0, min(0.99999, percentageVal))
            scaledVal = percentageValClamped * len(dataset)
            index = int(scaledVal)
            indexBy1 = min(index + 1, len(dataset) -1)
            lerpFactor = scaledVal % 1.0
            return dataset[indexBy1] * lerpFactor + dataset[index] * (1.0 - lerpFactor)

        # Add profile name to the list of loaded profiles
        if name in self.profileNames:
            self.error("Cannot register profile",name,"twice")
            return False
        profileIndex = len(self.profileNames)
        self.profileNames.append(name)

        # Generate gradient texture
        img = PNMImage(self.IESTableResolution, 1, 3, 2 ** 16 - 1)

        for offset in xrange(self.IESTableResolution):
            radialGradientVal = interpolateValue(lampRadialGradientData, offset / float(self.IESTableResolution))
            gradientVal = interpolateValue(lampGradientData, offset / float(self.IESTableResolution))

            img.setXel(offset, 0, radialGradientVal, gradientVal, 0)

        # Store gradient texture
        self.storage.load(img, profileIndex, 0)


    def _loadIESProfile(self, name, filename):
        """ Internal method to load an ies profile. Adapted from
        https://gist.githubusercontent.com/AngryLoki/4364512/raw/ies2cycles.py """
        self.debug("loading ies profile", filename)

        profileMultiplier = 1.0

        # Open the IES file
        with open(filename, 'rt') as handle:
            content = handle.read()

        # Extract and check version string
        versionString, content = content.split('\n', 1)

        if versionString in self.IESVersionTable:
            version = self.IESVersionTable[versionString]
        else:
            self.warn("No supported IES version found")
            version = None

        # Extract IES properties
        keywords = dict()
        while content and not content.startswith('TILT='):
            key, content = content.split('\n', 1)
            if key.startswith('['):
                endbracket = key.find(']')
                if endbracket != -1:
                    keywords[key[1:endbracket]] = key[endbracket + 1:].strip()

        # After all properties, the tile keyword should follow
        keyword, content = content.split('\n', 1)

        if not keyword.startswith('TILT'):
            self.warn("TILT keyword not found")
            return False

        # Strip data
        fileData = content.replace(',', ' ').split()

        # Property 0 is the amount of lamps
        numLamps = int(fileData[0])
        if numLamps != 1:
            self.warn("Only 1 lamp is supported,", numLamps, "found")

        # Extract further properties
        lumensPerLamp = float(fileData[1])
        candelaMultiplier = float(fileData[2])
        numVerticalAngles = int(fileData[3])
        numHorizontalAngles = int(fileData[4])

        # Check if everything went right so far
        if not numVerticalAngles or not numHorizontalAngles:
            self.error("Error during property extract")
            return False

        # Extract further properties
        photometricType = int(fileData[5])
        unitType = int(fileData[6])

        # Determine the unit type, either feet or meters
        if unitType not in [1, 2]:
            self.warn("Unkown unity type:", unitType)

        # Extract data size
        width, length, height = map(float, fileData[7:10])
        ballastFactor = float(fileData[10])

        futureUse = float(fileData[11])
        if futureUse != 1.0:
            self.warn("Invalid future use field")

        inputWatts = float(fileData[12])

        # Extract the actual data
        verticalAngles = [float(s) for s in fileData[13:13 + numVerticalAngles]]
        horizontalAngles = [float(s) for s in fileData[13 + numVerticalAngles:
                                              13 + numVerticalAngles + numHorizontalAngles]]

        # Determine the vertical light cone type. There are 90 and 180 degree cone types.
        if verticalAngles[0] == 0 and verticalAngles[-1] == 90:
            lampConeType = 'TYPE90'
        elif verticalAngles[0] == 0 and verticalAngles[-1] == 180:
            lampConeType = 'TYPE180'
        else:
            self.warn("Unsupported angles: ", verticalAngles[0], "-", verticalAngles[-1])
            lampConeType = 'TYPE180'

        # Determine the horizontal light cone type
        if len(horizontalAngles) == 1 or abs(horizontalAngles[0] - horizontalAngles[-1]) == 360:
            lampHorizontalConeType = 'TYPE360'
        elif abs(horizontalAngles[0] - horizontalAngles[-1]) == 180:
            lampHorizontalConeType = 'TYPE180'
        elif abs(horizontalAngles[0] - horizontalAngles[-1]) == 90:
            lampHorizontalConeType = 'TYPE90'
        else:
            self.warn("Unsupported horizontal angles: ", horizontalAngles[0], "-", horizontalAngles[-1])
            lampHorizontalConeType = 'TYPE360'
            
        # Read the candela values
        offset = 13 + len(verticalAngles) + len(horizontalAngles)
        candelaIndex = len(verticalAngles) * len(horizontalAngles)
        candelaValues = [float(s) for s in fileData[offset:offset + candelaIndex]]

        # Convert the 1d candela array to 2d array
        candela2D = list(zip(*[iter(candelaValues)] * len(verticalAngles)))

        # Compute the fallof gradient
        lampGradientData = [x / verticalAngles[-1] for x in verticalAngles]
       
        # Compute the radial gradient
        radialGradientData = [sum(x) / len(x) for x in zip(*candela2D)]
        radialGradientDataMax = max(radialGradientData)
        
        # Normalize the radial gradient by dividing by the maximum value
        radialGradientData = [val / radialGradientDataMax for val in radialGradientData]

        # Finally register the profile
        self._storeIESProfile(name, radialGradientData, lampGradientData)
        return True
