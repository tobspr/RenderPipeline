

from panda3d.core import Vec2, LVecBase2i
from DebugObject import DebugObject


class ShadowAtlas(DebugObject):

    """ This class manages the shadow atlas, used by LightManager.
    It supports reordering the atlas, for gaining more space,
    and also helps by fitting all shadow maps most efficiently
    into the atlas. """

    def __init__(self):
        """ Constructs a new shadow atlas """
        DebugObject.__init__(self, "ShadowAtlas")
        self.size = 512

    def create(self):
        """ Creates this atlas, also setting up the atlas texture """
        # Find a good tile size, it should not be too big but
        # also not too small
        self.tileSize = 32

        if self.size % self.tileSize is not 0:
            self.error(
                "Shadow map size has to be a multiple of", self.tileSize)
            return False

        while self.size / self.tileSize > 32:
            self.tileSize += 16

        self.tileCount = self.size / self.tileSize

        self.debug(
            "Creating atlas with size", self.size, "and tile size", self.tileSize)

        # Create binary tile representation
        self.tiles = [
            [None for x in range(self.tileCount)] for y in range(self.tileCount)]

    def setSize(self, size):
        """ Sets the shadow atlas size in pixels """
        assert(size >= 128 and size <= 8192)
        self.size = size

    def getSize(self):
        """ Returns the shadow atlas size in pixels """
        return self.size

    def getTileSize(self):
        """ Returns the size of a tile. Shadow maps must not be
        smaller than this """
        return self.tileSize

    def reserveTiles(self, width, height, tileIndex):
        """ Reserves enough tiles to store a tile with the ID tileIndex
        and the dimensions width*height in the atlas and returns the
        top-left coordinates of the reserved space """

        # Convert to tile space
        tileW, tileH = width / self.tileSize, height / self.tileSize

        # self.warn("Finding position for tile of size", tileW, "x", tileH)

        maxIterations = self.tileCount - tileW + 1, self.tileCount - tileH + 1
        tileFound = False
        tilePos = LVecBase2i(-1)

        # Iterate all tiles
        for j in range(0, maxIterations[0]):
            if not tileFound:
                for i in range(0, maxIterations[1]):
                    if not tileFound:

                        # First, assume the space is free
                        tileFree = True

                        # Now, check if anything is blocking the space, and if so,
                        # mark the tile as reserved
                        for x in range(tileW):
                            for y in range(tileH):
                                if not tileFree:
                                    break
                                if self.tiles[j + y][i + x] is not None:
                                    tileFree = False
                                    break

                        # When the tile is free, we have found our tile
                        if tileFree:
                            tileFound = True
                            tilePos = LVecBase2i(i, j)
                            break

        if tileFound:
            # self.debug("Tile #" + str(tileIndex) + " found:",
                       # tilePos.x * self.tileSize, "/", tilePos.y * self.tileSize)
            self._reserveTile(tilePos.x, tilePos.y, tileW, tileH, tileIndex)

            return Vec2(
                float(tilePos.x) / float(self.tileCount),
                float(tilePos.y) / float(self.tileCount))

        else:
            self.error("No free tile found! Have to update whole atlas maybe?")
            return None

    def _reserveTile(self,  offsetX, offsetY, width, height, value):
        """ Reserves the space of the size width*height at the position
        offsetX, offsetY in the atlas, setting their assigned index to value """
        for x in range(0, width):
            for y in range(0, height):
                self.tiles[y + offsetY][x + offsetX] = value
