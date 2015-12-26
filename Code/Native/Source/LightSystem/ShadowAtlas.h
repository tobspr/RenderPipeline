#ifndef RP_SHADOW_ATLAS_H
#define RP_SHADOW_ATLAS_H

#include "pandabase.h"
#include "lvecBase4.h"

NotifyCategoryDecl(shadowatlas, EXPORT_CLASS, EXPORT_TEMPL);


/**
 * @brief Class which manages distributing shadow maps in an atlas.
 * @details This class manages the shadow atlas. It handles finding and reserving
 *   space for new shadow maps.
 */
class ShadowAtlas {

PUBLISHED:
    ShadowAtlas(size_t size, size_t tile_size = 32);
    ~ShadowAtlas();

public:

    LVecBase4i find_and_reserve_region(size_t tile_width, size_t tile_height);
    void free_region(const LVecBase4i& region);
    inline LVecBase4f region_to_uv(const LVecBase4i& region);

    inline int get_tile_size() const;
    inline int get_required_tiles(size_t resolution) const;
protected:

    void init_tiles();
    
    inline void set_tile(size_t x, size_t y, bool flag);
    inline bool get_tile(size_t x, size_t y) const;

    inline bool region_is_free(size_t x, size_t y, size_t w, size_t h) const;
    void reserve_region(size_t x, size_t y, size_t w, size_t h);

    size_t _size;
    size_t _num_tiles;
    size_t _tile_size;
    bool* _flags;
};

#include "ShadowAtlas.I"


#endif // RP_SHADOW_ATLAS_H
