#ifndef RP_SHADOW_MANAGER_H
#define RP_SHADOW_MANAGER_H

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
#include "ShadowSource.h"

NotifyCategoryDecl(shadowmanager, EXPORT_CLASS, EXPORT_TEMPL);


class ShadowManager : public ReferenceCount {

    PUBLISHED:
        ShadowManager();
        ~ShadowManager();

        inline void set_max_updates(size_t max_updates);
        inline void set_atlas_size(size_t atlas_size);
        inline void set_scene(NodePath scene_parent);
        inline void set_tag_state_manager(TagStateManager* tag_mgr);
        inline void set_atlas_graphics_output(GraphicsOutput* graphics_output);

        inline size_t get_atlas_size() const;
        inline size_t get_num_update_slots_left() const;

        void init();
        void update();

    public:
        inline ShadowAtlas* get_atlas() const;
        inline bool add_update(const ShadowSource* source);

    private:
        size_t _max_updates;
        size_t _atlas_size;
        NodePath _scene_parent;

        pvector<PT(Camera)> _cameras;
        pvector<NodePath> _camera_nps;
        pvector<PT(DisplayRegion)> _display_regions;

        ShadowAtlas* _atlas;
        TagStateManager* _tag_state_mgr;
        GraphicsOutput* _atlas_graphics_output;
 
        typedef pvector<const ShadowSource*> UpdateQueue;
        UpdateQueue _queued_updates;
};

#include "ShadowManager.I"

#endif // RP_SHADOW_MANAGER_H
