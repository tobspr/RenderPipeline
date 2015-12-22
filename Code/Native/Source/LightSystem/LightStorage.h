
#ifndef RP_LIGHT_STORAGE_H
#define RP_LIGHT_STORAGE_H

#include "RPLight.h"
#include "ShadowSource.h"
#include "GPUCommandList.h"

#define MAX_LIGHT_COUNT 65000
#define MAX_SHADOW_SOURCES 1000

class LightStorage {

    PUBLISHED:
        LightStorage();
        ~LightStorage();

        void add_light(PT(RPLight) light);
        void remove_light(PT(RPLight) light);
        void set_command_list(GPUCommandList *cmd_list);

        void update();
        
        inline int get_max_light_index() const;
        inline int get_num_stored_lights() const;

    protected:
        
        void setup_shadows(RPLight* light);

        inline int find_light_slot() const;
        inline int find_shadow_slot() const;
        inline void update_max_light_index();
        inline void update_max_source_index();

        RPLight* _lights[MAX_LIGHT_COUNT];
        ShadowSource* _shadow_sources[MAX_SHADOW_SOURCES];

        int _max_light_index;
        int _num_stored_lights;

        int _max_source_index;
        int _num_stored_sources;

        GPUCommandList* _cmd_list;
};

#include "LightStorage.I"

#endif // RP_LIGHT_STORAGE_H
