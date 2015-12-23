

#include "LightStorage.h"


LightStorage::LightStorage() {

    // Allocate containers
    _lights = new RPLight*[MAX_LIGHT_COUNT];
    _shadow_sources = new ShadowSource*[MAX_SHADOW_SOURCES];
    
    // Reset containers
    for (int i = 0; i < MAX_LIGHT_COUNT; ++i)
        _lights[i] = NULL;
    for (int i = 0; i < MAX_SHADOW_SOURCES; ++i)
        _shadow_sources[i] = NULL;

    _num_stored_lights = 0;
    _max_light_index = 0;
    _max_source_index = 0;
    _num_stored_sources = 0;
    _cmd_list = NULL;
}

LightStorage::~LightStorage() {
    delete [] _lights;
    delete [] _shadow_sources;
}

void LightStorage::set_command_list(GPUCommandList *cmd_list) {
    _cmd_list = cmd_list;
}


void LightStorage::add_light(PT(RPLight) light) {
    if (light->has_slot()) {
        cerr << "LightStorage: cannot add light since it already has a slot!" << endl;
        return;
    }

    // Reference the light, since we store it
    light->ref();
    int slot = find_light_slot();

    // In case we found no slot, emit an error
    if (slot < 0) {
        cerr << "LightStorage: All light slots used!" << endl;
        return;
    }

    _num_stored_lights ++;
    _max_light_index = max(_max_light_index, slot);

    _lights[slot] = light;
    light->assign_slot(slot);
    light->unset_dirty_flag();

    // Light casts shadows
    if (light->get_casts_shadows()) {
        setup_shadows(light);
    }

    GPUCommand cmd_add(GPUCommand::CMD_store_light);
    light->write_to_command(cmd_add);
    _cmd_list->add_command(cmd_add);
}


void LightStorage::setup_shadows(RPLight* light) {
    cout << "setting up shadows for light" << endl;
    light->init_shadow_sources();

    for (int i = 0; i < light->get_num_shadow_sources(); ++i) {
        ShadowSource* source = light->get_shadow_source(i);
        
        int slot = find_shadow_slot();
        if (slot < 0) {
            cerr << "Could not attach shadow source, out of slots!" << endl;
            return;
        }   

        // Assign the slot
        _shadow_sources[slot] = source;
        source->set_slot(slot);

        // Update maximum source index
        _max_source_index = max(_max_source_index, slot);
    }
}


void LightStorage::remove_light(PT(RPLight) light) {
    if (!light->has_slot()) {
        cerr << "Cannot detach light, light has no slot!" << endl;
        return;
    }

    _lights[light->get_slot()] = NULL;

    GPUCommand cmd_remove(GPUCommand::CMD_remove_light);
    cmd_remove.push_int(light->get_slot());
    _cmd_list->add_command(cmd_remove);

    _num_stored_lights --;

    // Correct max light index
    if (light->get_slot() == _max_light_index) {
        update_max_light_index();
    }

    light->remove_slot();

    // TODO: Cleanup shadow sources

    // Since we referenced the light when we stored it, we
    // have to decrease the reference aswell
    light->unref();
}



void LightStorage::update() {

    // Find all dirty lights and update them
    for (int k = 0; k <= _max_light_index; ++k) {
        if (_lights[k] && _lights[k]->is_dirty()) {

            // Update shadow sources in case the light is dirty
            _lights[k]->update_shadow_sources();
            GPUCommand cmd_update(GPUCommand::CMD_store_light);
            _lights[k]->write_to_command(cmd_update);
            _lights[k]->unset_dirty_flag();
            _cmd_list->add_command(cmd_update);
        }
    }

    vector<ShadowSource*> _sources_to_update;
    _sources_to_update.reserve(_max_source_index);

    // Find all dirty shadow sources and make a list of them
    for (int k = 0; k <= _max_source_index; ++k) {
        if (_shadow_sources[k] && _shadow_sources[k]->needs_update()) {
            _sources_to_update.push_back(_shadow_sources[k]);

            // Since we will update the source, we will also find a new spot for it,
            // so unregister the old spot
            if (_shadow_sources[k]->has_region()) {
                cerr << "TODO: Free old region of shadow source in atlas" << endl;
            }
        }
    }

}
