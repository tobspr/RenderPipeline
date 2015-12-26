
inline int InternalLightManager::find_light_slot() const {
    // Find the first free slot
    for (size_t k = 0; k < MAX_LIGHT_COUNT; ++k) {
        if (_lights[k] == NULL)
            return k;
    }
    return -1;
}


inline int InternalLightManager::find_shadow_slot() const {
    // Find the first free slot
    for (size_t k = 0; k < MAX_SHADOW_SOURCES; ++k) {
        if (_shadow_sources[k] == NULL)
            return k;
    }
    return -1;
}

inline void InternalLightManager::update_max_light_index() {
    int curr = _max_light_index;
    while (!_lights[curr--]);
    _max_light_index = curr;
}

inline void InternalLightManager::update_max_source_index() {
    int curr = _max_source_index;
    while (!_shadow_sources[curr--]);
    _max_source_index = curr;
}



inline int InternalLightManager::get_max_light_index() const {
    return _max_light_index;
}

inline int InternalLightManager::get_num_stored_lights() const {
    return _num_stored_lights;
}

inline void InternalLightManager::set_shadow_manager(ShadowManager* mgr) {
    _shadow_manager = mgr;
}

inline void InternalLightManager::set_command_list(GPUCommandList *cmd_list) {
    _cmd_list = cmd_list;
}
