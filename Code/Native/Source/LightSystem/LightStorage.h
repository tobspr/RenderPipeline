
#ifndef RP_LIGHT_STORAGE_H
#define RP_LIGHT_STORAGE_H

#include "RPLight.h"
#include "GPUCommandList.h"

#define MAX_LIGHT_COUNT 65000

class LightStorage {

    PUBLISHED:
        LightStorage();
        ~LightStorage();

        void add_light(PT(RPLight) light);
        void remove_light(PT(RPLight) light);
        void set_command_list(GPUCommandList *cmd_list);

        void update();
        int get_max_light_index();
        int get_num_stored_lights();

    protected:
        
        RPLight* _lights[MAX_LIGHT_COUNT];
        int _max_light_index;
        int _num_stored_lights;
        GPUCommandList* _cmd_list;

};



#endif // RP_LIGHT_STORAGE_H