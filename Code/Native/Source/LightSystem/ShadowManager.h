
#ifndef SHADOW_MANAGER_H
#define SHADOW_MANAGER_H

#include "pandabase.h"
#include "camera.h"
#include "matrixLens.h"
#include "ShadowAtlas.h"
#include "referenceCount.h"

class ShadowManager : public ReferenceCount {

    PUBLISHED:
        ShadowManager();
        ~ShadowManager();

        inline void set_max_updates(size_t max_updates);
        inline void set_atlas_size(size_t atlas_size);

        void init();

    public:
        inline ShadowAtlas* get_atlas();

    private:
        size_t _max_updates;
        size_t _atlas_size;

        pvector<PT(Camera)> _camera_slots;
        ShadowAtlas* _atlas;
};


#include "ShadowManager.I"

#endif // SHADOW_MANAGER_H

