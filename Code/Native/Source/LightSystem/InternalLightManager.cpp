
#include "InternalLightManager.h"

NotifyCategoryDef(lightmgr, "");


InternalLightManager::InternalLightManager() {
    _cmd_list = NULL;
    _shadow_manager = NULL;
}

void InternalLightManager::add_light(PT(RPLight) light) {
    nassertv(_shadow_manager != NULL);

    if (light->has_slot()) {
        lightmgr_cat.error() << "InternalLightManager: cannot add light " 
                             << "since it already has a slot!" << endl;
        return;
    }

    // Reference the light because we store it
    light->ref();

    // Find a free slot
    size_t slot;
    if (!_lights.find_slot(slot)) {
        lightmgr_cat.error() << "All light slots used!" << endl;
    }

    // Reserve the slot
    light->assign_slot(slot);
    _lights.reserve_slot(slot, light);

    // Setup the shadows in case the light uses them
    if (light->get_casts_shadows()) {
        setup_shadows(light);
    }
}


void InternalLightManager::setup_shadows(RPLight* light) {
    light->init_shadow_sources();

    size_t num_sources = light->get_num_shadow_sources();
    size_t base_slot;
    if (!_shadow_sources.find_consecutive_slots(base_slot, num_sources)) {
        lightmgr_cat.error() << "Failed to find slot for shadow sources!" << endl;
        return;
    }

    for (int i = 0; i < num_sources; ++i) {
        ShadowSource* source = light->get_shadow_source(i);        
        size_t slot = base_slot + i;

        // Assign the slot
        _shadow_sources.reserve_slot(slot, source);
        source->set_slot(slot);
    }
}


void InternalLightManager::remove_light(PT(RPLight) light) {
    nassertv(_shadow_manager != NULL);
    
    if (!light->has_slot()) {
        lightmgr_cat.error() << "Cannot detach light, light has no slot!" << endl;
        return;
    }

    _lights.free_slot(light->get_slot());

    GPUCommand cmd_remove(GPUCommand::CMD_remove_light);
    cmd_remove.push_int(light->get_slot());
    _cmd_list->add_command(cmd_remove);

    light->remove_slot();

    for (size_t i = 0; i < light->get_num_shadow_sources(); ++i) {
        ShadowSource* source = light->get_shadow_source(i);
        if (source->has_slot()) {
            _shadow_sources.free_slot(source->get_slot());
        }
    }

    // TODO: Cleanup shadow sources - emit cmd_remove
    // GPUCommand cmd_remove_sources(GPUCommand::CMD_remove_sources);
    // cmmd_remove_sources.push_int(light->get_shadow_source(0)->get_slot());
    // cmmd_remove_sources.push_int(light->get_num_shadow_sources());

    // Since we referenced the light when we stored it, we
    // have to decrease the reference as well
    light->unref();
}


void InternalLightManager::update() {

    // Make sure we have a manager
    nassertv(_shadow_manager != NULL);

    // Find all dirty lights and update them
    for (auto iter = _lights.begin(); iter != _lights.end(); ++iter) {
        RPLight* light = *iter;
        if (light && light->is_dirty()) {

            // Update shadow sources in case the light is dirty
            light->update_shadow_sources();
            GPUCommand cmd_update(GPUCommand::CMD_store_light);
            cmd_update.push_int(light->get_slot());
            light->write_to_command(cmd_update);
            light->unset_dirty_flag();
            _cmd_list->add_command(cmd_update);
        }
    }

    vector<ShadowSource*> _sources_to_update;
    _sources_to_update.reserve(_max_source_index);

    // Find all dirty shadow sources and make a list of them
     for (auto iter = _shadow_sources.begin(); iter != _shadow_sources.end(); ++iter) {
        ShadowSource* source = *iter;
        if (source && source->get_needs_update()) {
            _sources_to_update.push_back(source);

            // Since we will update the source, we will also find a new spot for it,
            // so unregister the old spot
            if (source->has_region()) {
                _shadow_manager->get_atlas()->free_region(source->get_region());
            }
        }
    }

    // TODO: Sort the list of sources to update by their resolution, so that
    // big sources come first.

    // Now find an atlas spot for all regions
    for (size_t i = 0; i < _sources_to_update.size(); ++i) {
        ShadowSource *source = _sources_to_update[i];
        size_t num_tiles = _shadow_manager->get_atlas()->get_required_tiles(source->get_resolution());
        LVecBase4i new_region = _shadow_manager->get_atlas()->find_and_reserve_region(num_tiles, num_tiles);
        LVecBase4f new_region_uv = _shadow_manager->get_atlas()->region_to_uv(new_region);

        source->set_region(new_region, new_region_uv);

        if(_shadow_manager->add_update(source)) {

            // Update performed
            source->set_needs_update(false);

            // Also update the sources data on the GPU
            GPUCommand cmd_update_src(GPUCommand::CMD_store_source);
            cmd_update_src.push_int(source->get_slot());
            source->write_to_command(cmd_update_src);
            _cmd_list->add_command(cmd_update_src);

        } else {
            // Out of update slots. We can just abort the loop here.
            lightmgr_cat.warning() << "Aborting update, because out of update slots" << endl;
            break;
        }
    }
}
