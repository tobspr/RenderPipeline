
#ifndef SHADOW_ATLAS_H
#define SHADOW_ATLAS_H

#include "pandabase.h"
#include "lvecBase4.h"

class ShadowAtlas {

PUBLISHED:
    
    ShadowAtlas(size_t size);
    ~ShadowAtlas();

public:

    LVecBase4i find_and_reserve_region(size_t tile_width, size_t tile_height);
    void free_region(const LVecBase4i& region);

    inline int get_tile_size() const;
    inline int get_required_tiles(size_t resolution) const;

protected:

    inline void set_tile(size_t x, size_t y, bool flag);
    inline bool get_tile(size_t x, size_t y) const;

    void init_tiles();
    inline bool region_is_free(size_t x, size_t y, size_t w, size_t h) const;
    void reserve_region(size_t x, size_t y, size_t w, size_t h);

    size_t _size;
    size_t _num_tiles;
    size_t _tile_size;
    bool* _flags;
};

#include "ShadowAtlas.I"


#endif // SHADOW_ATLAS_H
