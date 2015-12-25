

inline int ShadowAtlas::get_tile_size() const {
    return _tile_size;
}


inline void ShadowAtlas::set_tile(size_t x, size_t y, bool flag) {
    // No bounds check for performance
    _flags[x + y * _num_tiles] = flag;
}

inline bool ShadowAtlas::get_tile(size_t x, size_t y) const {
    // No bounds check for performance
    return _flags[x + y * _num_tiles];
}

inline bool ShadowAtlas::region_is_free(size_t x, size_t y, size_t w, size_t h) const {

    // Check if we are out of bounds, this should be disabled for performance
    // reasons at some point.
    nassertr(x >= 0 && y >= 0 && x + w <= _num_tiles && y + h <= _num_tiles, false);

    // Iterate over every tile in that region and check if it is still free.
    for (size_t cx = 0; cx < w; ++cx) {
        for (size_t cy = 0; cy < h; ++cy) {
            if (get_tile(cx + x, cy + y)) return false;
        }
    }

    return true;
}

inline int ShadowAtlas::get_required_tiles(size_t resolution) const {
    if (resolution % _tile_size != 0) {
        cerr << "Resolution " << resolution << " is not a multiple of the shadow atlas tile size (" << _tile_size << ")!" << endl;
        return 1;
    }
    return resolution / _tile_size;
}

inline LVecBase4f ShadowAtlas::region_to_uv(const LVecBase4i& region) {
    LVecBase4f flt = LVecBase4f(region.get_x(), region.get_y(), region.get_z(), region.get_w());
    return flt * ((float)_tile_size / (float)_size);
}


