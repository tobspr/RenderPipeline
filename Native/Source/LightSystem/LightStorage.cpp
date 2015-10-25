

#include "LightStorage.h"


LightStorage::LightStorage() {
    for (int i = 0; i < MAX_LIGHT_COUNT; i++) {
        _lights[i] = nullptr;
    }
    _num_stored_lights = 0;
    _max_light_index = 0;
    _cmd_list = nullptr;
}


LightStorage::~LightStorage() {

}

void LightStorage::set_command_list(GPUCommandList *cmd_list) {
    _cmd_list = cmd_list;
}

int LightStorage::get_max_light_index() {
    return _max_light_index;
}



void LightStorage::add_light(PT(RPLight) light) {
    if (light->has_slot()) {
        cerr << "LightStorage: cannot add light since it already has a slot!" << endl;
        return;
    }

    // Reference the light, since we store it
    light->ref();
    //cout << "Add light: " << light << " -> " << light->get_ref_count() << endl;

    // Find the first free slot
    int slot = -1;
    for (size_t k = 0; k < MAX_LIGHT_COUNT; k++) {
        if (_lights[k] == nullptr) {
            slot = k;
            break;
        }
    }

    if (slot < 0) {
        cerr << "LightStorage: All light slots used!" << endl;
        return;
    }

    _num_stored_lights ++;

    _max_light_index = max(_max_light_index, slot);

    _lights[slot] = light;
    light->assign_slot(slot);
    light->unset_dirty_flag();

    GPUCommand cmd_add(GPUCommand::CMD_store_light);
    light->write_to_command(cmd_add);
    _cmd_list->add_command(cmd_add);
}

void LightStorage::remove_light(PT(RPLight) light) {
    if (!light->has_slot()) {
        cerr << "Cannot detach light, light has no slot!" << endl;
        return;
    }

    _lights[light->get_slot()] = nullptr;

    GPUCommand cmd_remove(GPUCommand::CMD_remove_light);
    cmd_remove.push_int(light->get_slot());
    _cmd_list->add_command(cmd_remove);

    _num_stored_lights --;

    // Correct max light index
    if (light->get_slot() == _max_light_index) {
       
        int curr = _max_light_index;
        while (!_lights[curr--]);
        _max_light_index = curr;
    }

    light->remove_slot();

    // Since we referenced the light when we stored it, we
    // have to decrease the reference aswell
    light->unref();

}

int LightStorage::get_num_stored_lights() {
    return _num_stored_lights;
}

void LightStorage::update() {

    // Find all dirty lights and update them
    for (int k = 0; k <= _max_light_index; k++) {
        if (_lights[k] && _lights[k]->is_dirty()) {
            GPUCommand cmd_update(GPUCommand::CMD_store_light);
            _lights[k]->write_to_command(cmd_update);
            _lights[k]->unset_dirty_flag();
            _cmd_list->add_command(cmd_update);
        }
    }
}
