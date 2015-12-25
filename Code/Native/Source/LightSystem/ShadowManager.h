
#ifndef SHADOW_MANAGER_H
#define SHADOW_MANAGER_H

#include "pandabase.h"
#include "camera.h"
#include "luse.h"
#include "matrixLens.h"
#include "ShadowAtlas.h"
#include "referenceCount.h"
#include "nodePath.h"
#include "TagStateManager.h"
#include "displayRegion.h"
#include "graphicsOutput.h"

class ShadowManager : public ReferenceCount {

    PUBLISHED:
        ShadowManager();
        ~ShadowManager();

        inline void set_max_updates(size_t max_updates);
        inline void set_atlas_size(size_t atlas_size);

        inline void set_scene(NodePath scene_parent);
        inline void set_tag_state_manager(TagStateManager* tag_mgr);

        inline void set_atlas_graphics_output(GraphicsOutput* graphics_output);

        void init();
        void update();

    public:
        inline ShadowAtlas* get_atlas();

        bool add_update(const LMatrix4f& mvp, const LVecBase4i& region);

    private:
        size_t _max_updates;
        size_t _atlas_size;

        pvector<PT(Camera)> _camera_slots;
        pvector<NodePath> _camera_nps;
        pvector<PT(DisplayRegion)> _display_regions;

        ShadowAtlas* _atlas;
        TagStateManager* _tag_state_mgr;

        GraphicsOutput* _atlas_graphics_output;

        NodePath _scene_parent;

        struct ShadowUpdate {
            LMatrix4f mvp;
            LVecBase4f uv;

            ShadowUpdate(const LMatrix4f& mvp_, const LVecBase4f& uv_) : mvp(mvp_), uv(uv_) {};
        };

        typedef pvector<ShadowUpdate> UpdateQueue;
        UpdateQueue _queued_updates;

};


#include "ShadowManager.I"

#endif // SHADOW_MANAGER_H

