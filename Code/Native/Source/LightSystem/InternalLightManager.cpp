
#include "InternalLightManager.h"

#include <algorithm>

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

    // Store the light on the gpu
    gpu_update_light(light);
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
        source->set_needs_update(true);

        // Assign the slot
        size_t slot = base_slot + i;
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
    gpu_remove_light(light);
    light->remove_slot();

    if (light->get_casts_shadows()) {

        // Free the slots of all sources, and also unregister their regions from
        // the shadow atlas.
        for (size_t i = 0; i < light->get_num_shadow_sources(); ++i) {
            ShadowSource* source = light->get_shadow_source(i);
            if (source->has_slot()) {
                _shadow_sources.free_slot(source->get_slot());
            }
            if (source->has_region()) {
                _shadow_manager->get_atlas()->free_region(source->get_region());
            }
        }

        // Remove all sources of the light by emitting a consecutive remove command
        gpu_remove_consecutive_sources(light->get_shadow_source(0),
                                       light->get_num_shadow_sources());

        light->clear_shadow_sources();
    }

    // Since we referenced the light when we stored it, we
    // have to decrease the reference as well
    light->unref();
}

void InternalLightManager::gpu_remove_consecutive_sources(ShadowSource *first_source,
                                                          size_t num_sources) {
    GPUCommand cmd_remove(GPUCommand::CMD_remove_sources);
    cmd_remove.push_int(first_source->get_slot());
    cmd_remove.push_int(num_sources);
    _cmd_list->add_command(cmd_remove);
}

void InternalLightManager::gpu_remove_light(RPLight* light) {
    nassertv(_cmd_list != NULL);
    nassertv(light->has_slot());
    GPUCommand cmd_remove(GPUCommand::CMD_remove_light);
    cmd_remove.push_int(light->get_slot());
    _cmd_list->add_command(cmd_remove);
}

void InternalLightManager::gpu_update_light(RPLight* light) {
    nassertv(_cmd_list != NULL);
    nassertv(light->has_slot());
    GPUCommand cmd_update(GPUCommand::CMD_store_light);
    cmd_update.push_int(light->get_slot());
    light->write_to_command(cmd_update);
    light->unset_dirty_flag();
    _cmd_list->add_command(cmd_update);
}

void InternalLightManager::gpu_update_source(ShadowSource* source) {
    nassertv(_cmd_list != NULL);
    GPUCommand cmd_update(GPUCommand::CMD_store_source);
    cmd_update.push_int(source->get_slot());
    source->write_to_command(cmd_update);
    _cmd_list->add_command(cmd_update);
}

void InternalLightManager::update_lights() {
    for (auto iter = _lights.begin(); iter != _lights.end(); ++iter) {
        RPLight* light = *iter;
        if (light && light->is_dirty()) {
            light->update_shadow_sources();
            gpu_update_light(light);
        }
    }
}


void InternalLightManager::update_shadow_sources() {

    // Find all dirty shadow sources and make a list of them
    vector<ShadowSource*> _sources_to_update;

     for (auto iter = _shadow_sources.begin(); iter != _shadow_sources.end(); ++iter) {
        ShadowSource* source = *iter;
        if (source && source->get_needs_update()) {
            _sources_to_update.push_back(source);
        }
    }

    // Sort the sources based on their resolution, so that sources with a bigger
    // resolution come first. This helps to get a better packing on the shadow atlas.
    auto cmp_source = [](ShadowSource* a, ShadowSource* b){ return a->get_resolution() > b->get_resolution(); };
    std::sort(_sources_to_update.begin(), _sources_to_update.end(), cmp_source);

    // Get a handle to the atlas, will be frequently used
    ShadowAtlas *atlas = _shadow_manager->get_atlas();

    // Free the regions of all sources which will get updated. We have to take into
    // account that only a limited amount of sources can get updated per frame.
    size_t update_slots = min(_sources_to_update.size(),
                                   _shadow_manager->get_num_update_slots_left());
    for(size_t i = 0; i < update_slots; ++i) {
        if (_sources_to_update[i]->has_region()) {
           atlas->free_region(_sources_to_update[i]->get_region());
        }
    }

    // Find an atlas spot for all regions
    for (size_t i = 0; i < update_slots; ++i) {
        ShadowSource *source = _sources_to_update[i];

        if(!_shadow_manager->add_update(source)) {
            // In case the ShadowManager lied about the number of updates left
            lightmgr_cat.error() << "ShadowManager ensured update slot, but slot is taken!" << endl;
            break;
        }

        // We have an update slot, and are guaranteed to get updated as soon
        // as possible, so we can start getting a new atlas position.
        size_t region_size = atlas->get_required_tiles(source->get_resolution());
        LVecBase4i new_region = atlas->find_and_reserve_region(region_size, region_size);
        LVecBase4f new_uv_region = atlas->region_to_uv(new_region);
        source->set_region(new_region, new_uv_region);
        
        // Mark the source as updated
        source->set_needs_update(false);
        gpu_update_source(source);
    }
}

void InternalLightManager::update() {
    nassertv(_shadow_manager != NULL); // Not initialized yet!
    nassertv(_cmd_list != NULL);       // Not initialized yet!

    update_lights();
    update_shadow_sources();
}
