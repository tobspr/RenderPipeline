
inline int LightStorage::find_light_slot() {
    // Find the first free slot
    for (size_t k = 0; k < MAX_LIGHT_COUNT; k++) {
        if (_lights[k] == NULL)
            return k;
    }
    return -1;
}

inline void LightStorage::update_max_light_index() {
    int curr = _max_light_index;
    while (!_lights[curr--]);
    _max_light_index = curr;
}

