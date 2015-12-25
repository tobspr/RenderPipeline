
#include "TagStateManager.h"

TagStateManager::TagStateManager(NodePath main_cam_node) {
    nassertv(!main_cam_node.is_empty());
    nassertv(DCAST(Camera, main_cam_node.node()) != NULL);
    _main_cam_node = main_cam_node;


    // Set default mask
    DCAST(Camera, _main_cam_node.node())->set_camera_mask(get_gbuffer_mask());
}

TagStateManager::~TagStateManager() {
    cleanup_states();
    _tag_states.clear();
}

void TagStateManager::apply_shadow_state(NodePath np, Shader* shader, const string &name, int sort) {
    cout << "TagStateManager: Constructing new state: " << name << endl;

    // Construct the new state
    CPT(RenderState) state = RenderState::make_empty();
    state = state->set_attrib(ColorWriteAttrib::make(ColorWriteAttrib::C_off), 10000);
    state = state->set_attrib(ShaderAttrib::make(shader, sort), sort);

    // Store the state
    if (_tag_states.count(name)) {
        cout << "TagStateManager: Warning: Overriding existing state " << name << endl;
    }
    _tag_states[name] = state;

    // Save the tag on the node path
    np.set_tag(get_shadow_tag(), name);

    // Apply the state on all cameras attached so far
    for (CameraList::iterator iter = _shadow_cameras.begin(); iter != _shadow_cameras.end(); ++iter) {
        // cout << "Applied tag state " << name << " on camera " << *(*iter) << endl;
        (*iter)->set_tag_state(name, state);
    }
}

void TagStateManager::cleanup_states() {
    cout << "TagStateManager: cleaning up states" << endl;

    // Clear all tag states of the main camera
    DCAST(Camera, _main_cam_node.node())->clear_tag_states();

    // Clear all tag states of the shadow cameras
    for (CameraList::iterator iter = _shadow_cameras.begin(); iter != _shadow_cameras.end(); ++iter) {
        (*iter)->clear_tag_states();
    }

    _tag_states.clear();
}

void TagStateManager::register_shadow_camera(Camera* source) {
    source->set_tag_state_key(get_shadow_tag());
    source->set_camera_mask(get_shadow_mask());
    _shadow_cameras.push_back(source);
    cout << "TagStateManager: registered shadow camera:" << *source << endl;
}

void TagStateManager::unregister_shadow_camera(Camera* source) {
    // cout << "TagStateManager: unregistered shadow camera: " << *source << endl;
    _shadow_cameras.erase(
        std::remove(_shadow_cameras.begin(), _shadow_cameras.end(), source), _shadow_cameras.end()); 
}
