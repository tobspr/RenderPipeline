
#include "ShadowAtlas.h"


ShadowAtlas::ShadowAtlas(size_t size) {
    _size = size;
    _tile_size = 32;
    nassertv(_size % _tile_size == 0);
    init_tiles();
}

ShadowAtlas::~ShadowAtlas() {
    delete [] _flags;
}

void ShadowAtlas::init_tiles() {
    _num_tiles = _size / _tile_size;
    _flags = new bool[_num_tiles * _num_tiles];

    // Initialize all tiles to zero
    for (size_t i = 0; i < _num_tiles * _num_tiles; ++i) {
        _flags[i] = false;
    }
}

void ShadowAtlas::reserve_region(size_t x, size_t y, size_t w, size_t h) {

    // Check if we are out of bounds, this should be disabled for performance
    // reasons at some point.
    nassertv(x >= 0 && y >= 0 && x + w < _num_tiles && y + h < _num_tiles);

    // Iterate over every tile in the region and mark it as used
    for (size_t cx = 0; cx < w; ++cx) {
        for (size_t cy = 0; cy < h; ++cy) {
            set_tile(cx + x, cy + y, true);
        }
    }
}

LVecBase4i ShadowAtlas::find_and_reserve_region(size_t tile_width, size_t tile_height) {
    if (tile_width > _num_tiles || tile_height > _num_tiles) {
        cerr << "Requested region exceeds shadow atlas size!" << endl;
        return LVecBase4i(-1);
    }

    // Iterate over every possible region and check if its still free
    for (size_t x = 0; x < _num_tiles - tile_width; ++x) {
        for (size_t y = 0; y < _num_tiles - tile_height; ++y) {
            if (region_is_free(x, y, tile_width, tile_height)) {
                // Found free region, now reserve it
                reserve_region(x, y, tile_width, tile_height);
                // cout << "Found region at "<< x << " / " << y << " with size " << tile_width << " x " << tile_height << endl;
                return LVecBase4i(x, y, tile_width, tile_height);
            }
        }
    }


    cerr << "Failed to find a free region in the shadow atlas!" << endl;
    return LVecBase4i(-1);
}

void ShadowAtlas::free_region(const LVecBase4i& region) {
    // Out of bounds check, can't hurt
    nassertv(region.get_x() >= 0 && region.get_y() >= 0);
    nassertv(region.get_x() + region.get_z() < _num_tiles && region.get_y() + region.get_w() < _num_tiles);

    for (size_t x = 0; x < region.get_z(); ++x) {
        for (size_t y = 0; y < region.get_w(); ++y) {
            // Could do an assert here, that the tile should have been used (=true) before
            set_tile(region.get_x() + x, region.get_y() + y, false);
        }
    }
}
