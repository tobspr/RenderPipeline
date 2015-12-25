


inline void ShadowManager::set_max_updates(size_t max_updates) {
    nassertv(max_updates >= 0);
    if (max_updates == 0) {
        cout << "ShadowManager: Warning: max_updates set to 0, no shadows will be updated." << endl;
    }
    _max_updates = max_updates;
}

inline void ShadowManager::set_atlas_size(size_t atlas_size) {
    nassertv(atlas_size >= 128 && atlas_size <= 16384);
    _atlas_size = atlas_size;
}

inline ShadowAtlas* ShadowManager::get_atlas() {
    nassertr(_atlas != NULL, NULL); // Can't hurt to check
    return _atlas;
}

