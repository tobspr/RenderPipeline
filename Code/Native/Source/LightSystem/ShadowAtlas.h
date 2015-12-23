
#ifndef SHADOW_ATLAS_H
#define SHADOW_ATLAS_H

#include "pandabase.h"
#include "lvecBase2.h"

class ShadowAtlas {

PUBLISHED:
    
    ShadowAtlas(size_t size);
    ~ShadowAtlas();

    LVecBase2i find_and_reserve_free_region(size_t tile_width, size_t tile_height);

    inline int get_tile_size() const;

protected:

    void init_tiles();
    bool region_is_free(size_t x, size_t y, size_t w, size_t h);
    void reserve_region(size_t x, size_t y, size_t w, size_t h);

    size_t _size;
    size_t _num_tiles;
    size_t _tile_size;
    bool* _flags;
};

#include "ShadowAtlas.I"


#endif // SHADOW_ATLAS_H
