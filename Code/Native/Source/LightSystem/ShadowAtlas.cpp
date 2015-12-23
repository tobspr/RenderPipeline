
#include "ShadowAtlas.h"


ShadowAtlas::ShadowAtlas(size_t size) {
    _size = size;
    _tile_size = 64;
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

bool ShadowAtlas::region_is_free(size_t x, size_t y, size_t w, size_t h) {

    // Check if we are out of bounds, this should be disabled for performance
    // reasons at some point.
    nassertr(x >= 0 && y >= 0 && x + w < _num_tiles && y + h < _num_tiles, false);

    // Iterate over every tile in that region and check if it is still free.
    for (size_t cx = 0; cx < w; ++cx) {
        for (size_t cy = 0; cy < h; ++cy) {
            if (_flags[cx + x + (cy + h) * _num_tiles]) return false;
        }
    }

    return true;
}

void ShadowAtlas::reserve_region(size_t x, size_t y, size_t w, size_t h) {

    // Check if we are out of bounds, this should be disabled for performance
    // reasons at some point.
    nassertv(x >= 0 && y >= 0 && x + w < _num_tiles && y + h < _num_tiles);

    // Iterate over every tile in the region and mark it as used
    for (size_t cx = 0; cx < w; ++cx) {
        for (size_t cy = 0; cy < h; ++cy) {
            _flags[cx + x + (cy + h) * _num_tiles] = true;
        }
    }    
}


LVecBase2i ShadowAtlas::find_and_reserve_free_region(size_t tile_width, size_t tile_height) {
    if (tile_width > _num_tiles || tile_height > _num_tiles) {
        cerr << "Requested region exceeds shadow atlas size!" << endl;
        return LVecBase2i(-1);
    }

    // Iterate over every possible region and check if its still free
    for (size_t x = 0; x < _num_tiles - tile_width; ++x) {
        for (size_t y = 0; y < _num_tiles - tile_height; ++y) {
            if (region_is_free(x, y, tile_width, tile_height)) {
                // Found free region, now reserve it
                reserve_region(x, y, tile_width, tile_height);
                cout << "Found region at "<< x << " / " << y << endl;
                return LVecBase2i(x, y);
            }
        }
    }


    cerr << "Failed to find a free region in the shadow atlas!" << endl;
    return LVecBase2i(-1);
}
