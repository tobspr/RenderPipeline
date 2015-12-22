
#ifndef TAG_STATE_MANAGER_H
#define TAG_STATE_MANAGER_H

#include "pandabase.h"
#include "bitMask.h"
#include "camera.h"
#include "weakPointerTo.h"
#include "nodePath.h"
#include "shader.h"
#include "renderState.h"
#include "shaderAttrib.h"
#include "colorWriteAttrib.h"

class TagStateManager {

    PUBLISHED:
        TagStateManager(NodePath main_cam_node);
        ~TagStateManager();

        inline static BitMask32 get_gbuffer_mask();
        inline static BitMask32 get_voxelize_mask();
        inline static BitMask32 get_shadow_mask();

        void apply_shadow_state(NodePath np, Shader* shader, const string &name, int sort);
        void cleanup_states();
        
        void register_shadow_camera(Camera* source);
        void unregister_shadow_camera(Camera* source);

    public:

        inline static string get_shadow_tag();
        inline static string get_voxelize_tag();

    protected:

        typedef vector<Camera*> CameraList;
        typedef pmap<string, CPT(RenderState) > TagStateList;

        NodePath _main_cam_node;
        CameraList _shadow_cameras;
        TagStateList _tag_states;
};


#include "TagStateManager.I"

#endif // TAG_STATE_MANAGER_H


