
#ifndef SHADOW_SOURCE_H
#define SHADOW_SOURCE_H

#include "pandabase.h"
#include "luse.h"
#include "transformState.h"
#include "look_at.h"
#include "compose_matrix.h"
#include "perspectiveLens.h"
#include "GPUCommand.h"

class ShadowSource {

public: 
    ShadowSource();
    ~ShadowSource();

    inline void invalidate();
    inline bool needs_update() const;
    inline void on_update_done();

    inline void write_to_command(GPUCommand &cmd);

    inline void set_slot(int slot);
    inline void set_region(LVecBase4i region, LVecBase4f region_uv);
    inline void set_resolution(size_t resolution);
    inline void set_perspective_lens(float fov, float near_plane, float far_plane, LVecBase3f pos, LVecBase3f direction);

    inline bool has_region() const;
    inline bool has_slot() const;

    inline int get_slot() const;
    inline const LVecBase4i& get_region() const;
    inline size_t get_resolution() const;

    inline const LMatrix4f& get_mvp() const;

private:
    LMatrix4f _mvp;
    int _slot;
    bool _needs_update;
    size_t _resolution;
    LVecBase4i _region;
    LVecBase4f _region_uv;
};



#include "ShadowSource.I"

#endif // SHADOW_SOURCE_H
