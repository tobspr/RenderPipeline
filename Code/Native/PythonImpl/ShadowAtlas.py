
from __future__ import print_function, division
from six.moves import range

from panda3d.core import LVecBase4i, LVecBase4

class ShadowAtlas(object):
    
    def __init__(self, size, tile_size = 32):
        self._size = size
        self._tile_size = tile_size
        self.init_tiles()

    def init_tiles(self):
        self._num_tiles = self._size // self._tile_size
        self._flags = [ [False for j in range(self._num_tiles)] for i in range(self._num_tiles)]

    def reserve_region(self, x, y, w, h):
        for cx in range(w):
            for cy in range(h):
                self._flags[cx + x][cy + y] = True

    def find_and_reserve_region(self, tile_width, tile_height):
        for x in range(self._num_tiles - tile_height + 1):
            for y in range(self._num_tiles - tile_width + 1):
                if self.region_is_free(x, y, tile_width, tile_height):
                    self.reserve_region(x, y, tile_width, tile_height)
                    return LVecBase4i(x, y, tile_width, tile_height)
        print("Failed to find a free region of size", tile_width, "x", tile_height)
        return LVecBase4i(-1)

    def free_region(self, region):
        for x in range(region.z):
            for y in range(region.w):
                self._flags[region.x + x][region.y + y] = False

    def get_tile_size(self):
        return self._tile_size

    def region_is_free(self, x, y, w, h):
        for cx in range(w):
            for cy in range(h):
                if self._flags[cx + x][cy + y]:
                    return False
        return True

    def get_required_tiles(self, resolution):
        if resolution % self._tile_size != 0:
            print("ShadowAtlas: Invalid atlas resolution!")
            return
        return resolution // self._tile_size

    def region_to_uv(self, region):
        flt = LVecBase4(region.x, region.y, region.z, region.w)
        return flt * (self._tile_size / self._size)

