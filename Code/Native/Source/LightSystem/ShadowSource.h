
#ifndef SHADOW_SOURCE_H
#define SHADOW_SOURCE_H

#include "pandabase.h"
#include "transformState.h"
#include "look_at.h"
#include "compose_matrix.h"

class ShadowSource {

public: 
    ShadowSource();
    ~ShadowSource();

    inline void invalidate();
    inline bool needs_update() const;

    inline int get_slot() const;
    inline void set_slot(int slot);

    inline void set_pos_dir(LVecBase3f pos, LVecBase3f direction);

private:

    LMatrix4f _transform;
    int _last_time_rendered;
    int _slot;
    bool _needs_update;
};



#include "ShadowSource.I"

#endif // SHADOW_SOURCE_H
