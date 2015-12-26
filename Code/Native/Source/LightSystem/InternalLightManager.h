#ifndef RP_INTERNAL_LIGHT_MANAGER_H
#define RP_INTERNAL_LIGHT_MANAGER_H

#include "RPLight.h"
#include "ShadowSource.h"
#include "ShadowAtlas.h"
#include "GPUCommandList.h"
#include "ShadowManager.h"
#include "referenceCount.h"
#include "PointerSlotStorage.h"

#define MAX_LIGHT_COUNT 65535
#define MAX_SHADOW_SOURCES 2048

NotifyCategoryDecl(lightmgr, EXPORT_CLASS, EXPORT_TEMPL);

class InternalLightManager : public ReferenceCount {

    PUBLISHED:
        InternalLightManager();

        void add_light(PT(RPLight) light);
        void remove_light(PT(RPLight) light);

        void update();
        
        inline int get_max_light_index() const;
        inline int get_num_stored_lights() const;

        inline void set_command_list(GPUCommandList *cmd_list);
        inline void set_shadow_manager(ShadowManager* mgr);

    protected:
        
        void setup_shadows(RPLight* light);

        inline int find_light_slot() const;
        inline int find_shadow_slot() const;
        inline void update_max_light_index();
        inline void update_max_source_index();

        GPUCommandList* _cmd_list;
        ShadowManager* _shadow_manager;

        PointerSlotStorage<RPLight*, MAX_LIGHT_COUNT> _lights;
        PointerSlotStorage<ShadowSource*, MAX_SHADOW_SOURCES> _shadow_sources;

};

#include "InternalLightManager.I"

#endif // RP_INTERNAL_LIGHT_MANAGER_H
