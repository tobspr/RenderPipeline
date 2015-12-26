

inline int InternalLightManager::get_max_light_index() const {
    return _lights.get_max_index();
}

inline int InternalLightManager::get_num_stored_lights() const {
    return _lights.get_num_entries();
}

inline void InternalLightManager::set_shadow_manager(ShadowManager* mgr) {
    _shadow_manager = mgr;
}

inline void InternalLightManager::set_command_list(GPUCommandList *cmd_list) {
    _cmd_list = cmd_list;
}
