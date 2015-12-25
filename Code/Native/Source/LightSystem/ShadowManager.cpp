
#include "ShadowManager.h"


ShadowManager::ShadowManager() {
    _max_updates = 10;
    _atlas = NULL;
    _atlas_size = 4096;
    _tag_state_mgr = NULL;
    _atlas_graphics_output = NULL;
}

ShadowManager::~ShadowManager() {
    delete _atlas;

    // Todo: Could eventually unregister all shadow cameras. Since the tag state
    // manager does this on cleanup already, and we get destructed at the same
    // time, this is not really necessary
}


void ShadowManager::init() {
    nassertv(!_scene_parent.is_empty());
    nassertv(_tag_state_mgr != NULL);
    nassertv(_atlas_graphics_output != NULL);

    // Create the dummy cameras
    _camera_slots.resize(_max_updates);
    _camera_nps.reserve(_max_updates);
    for(size_t i = 0; i < _max_updates; ++i) {
        _camera_slots[i] = new Camera("ShadowCamPrefab-" + to_string(i));
        _camera_slots[i]->set_lens(new MatrixLens());
        _camera_slots[i]->set_active(false);
        _camera_slots[i]->set_scene(_scene_parent);
        _tag_state_mgr->register_shadow_camera(_camera_slots[i]);
        _camera_nps.push_back(_scene_parent.attach_new_node(_camera_slots[i]));
    }

    // Create the display regions
    _display_regions.resize(_max_updates);
    for (size_t i = 0; i < _max_updates; ++i) {
        PT(DisplayRegion) region = _atlas_graphics_output->make_display_region();
        region->set_sort(1000);
        region->set_clear_depth_active(true);
        region->set_clear_depth(1.0);
        region->set_clear_color_active(false);
        region->set_camera(_camera_nps[i]);
        region->set_active(false);
        _display_regions[i] = region;
    }

    // Create the atlas
    _atlas = new ShadowAtlas(_atlas_size);

    // Reserve enough space already
    _queued_updates.reserve(_max_updates);
}


void ShadowManager::update() {
    nassertv(_atlas != NULL);

    // Disable all cameras and regions which will not be used
    for (size_t i = _queued_updates.size(); i < _max_updates; ++i) {
        _camera_slots[i]->set_active(false);
        _display_regions[i]->set_active(false);
    }

    // This should be already ensured in add_update, but can't hurt to check
    nassertv(_queued_updates.size() <= _max_updates);

    for (size_t i = 0; i < _queued_updates.size(); ++i) {
        ShadowUpdate& update = _queued_updates[i];
        
        // Enable the slots
        _camera_slots[i]->set_active(true);
        _display_regions[i]->set_active(true);
        
        // Set the mvp and uv
        DCAST(MatrixLens, _camera_slots[i]->get_lens())->set_user_mat(update.mvp);
        _camera_slots[i]->show_frustum();

        _display_regions[i]->set_dimensions(
            update.uv.get_x(),                         // left
            update.uv.get_x() + update.uv.get_z(),    // right
            update.uv.get_y(),                       // bottom
            update.uv.get_y() + update.uv.get_w()   // top
        );

    }

    // Clear update list
    _queued_updates.clear();
    _queued_updates.reserve(_max_updates);
}


bool ShadowManager::add_update(const LMatrix4f& mvp, const LVecBase4i& region) {
    nassertr(_atlas != NULL, false);

    if (_queued_updates.size() >= _max_updates) {
        cerr << "ShadowManager: cannot update source, out of update slots" << endl;
        return false;
    }

    LVecBase4f uv = _atlas->region_to_uv(region);
    cout << "ShadowManager: Adding update: " << mvp << " to region " << region << "(uv = " << uv << ")" << endl;
    
    _queued_updates.push_back(ShadowUpdate(mvp, uv));

    return true;
}
