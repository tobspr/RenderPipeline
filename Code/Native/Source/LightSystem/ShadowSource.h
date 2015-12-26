
#ifndef RP_SHADOW_SOURCE_H
#define RP_SHADOW_SOURCE_H

#include "pandabase.h"
#include "luse.h"
#include "transformState.h"
#include "look_at.h"
#include "compose_matrix.h"
#include "perspectiveLens.h"
#include "GPUCommand.h"

/**
 * @brief This class represents a single shadow source.
 * @details The ShadowSource can be seen as a Camera. It is used by the Lights
 *   to render their shadows. Each ShadowSource has a position in the atlas,
 *   and a view-projection matrix. The shadow manager regenerates the shadow maps
 *   using the data from the shadow sources.
 */
class ShadowSource {

public: 
    ShadowSource();

    inline void write_to_command(GPUCommand &cmd) const;

    inline void set_needs_update(bool flag);
    inline void set_slot(int slot);
    inline void set_region(const LVecBase4i& region, const LVecBase4f& region_uv);
    inline void set_resolution(size_t resolution);
    inline void set_perspective_lens(float fov, float near_plane,
                                     float far_plane, LVecBase3f pos, LVecBase3f direction);
    inline void set_matrix_lens(const LMatrix4f& mvp);

    inline bool has_region() const;
    inline bool has_slot() const;

    inline int get_slot() const;
    inline bool get_needs_update() const;
    inline size_t get_resolution() const;
    inline const LMatrix4f& get_mvp() const;
    inline const LVecBase4i& get_region() const;

private:
    int _slot;
    bool _needs_update;
    size_t _resolution;
    LMatrix4f _mvp;
    LVecBase4i _region;
    LVecBase4f _region_uv;
};

#include "ShadowSource.I"

#endif // RP_SHADOW_SOURCE_H
