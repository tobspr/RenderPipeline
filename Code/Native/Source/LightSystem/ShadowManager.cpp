
#include "ShadowManager.h"


ShadowManager::ShadowManager() {
    _max_updates = 10;
    _atlas = NULL;
    _atlas_size = 4096;
}

ShadowManager::~ShadowManager() {
    delete _atlas;
}


void ShadowManager::init() {

    // Create the dummy cameras
    _camera_slots.resize(_max_updates);
    for(size_t i = 0; i < _max_updates; ++i) {
        _camera_slots[i] = new Camera("ShadowCamPrefab-" + to_string(i));
        _camera_slots[i]->set_lens(new MatrixLens());
    };

    // Create the atlas
    _atlas = new ShadowAtlas(_atlas_size);

}
