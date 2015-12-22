
inline BitMask32 TagStateManager::get_gbuffer_mask() {
    return BitMask32::bit(1);
}

inline BitMask32 TagStateManager::get_shadow_mask() {
    return BitMask32::bit(2);
}

inline BitMask32 TagStateManager::get_voxelize_mask() {
    return BitMask32::bit(3);
}

inline string TagStateManager::get_shadow_tag() {
    return "Shadows";
}

inline string TagStateManager::get_voxelize_tag() {
    return "Voxelize";
}

