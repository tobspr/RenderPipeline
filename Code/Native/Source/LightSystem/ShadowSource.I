


inline void ShadowSource::invalidate() {
    _needs_update = true;
}

inline bool ShadowSource::needs_update() const {
    return _needs_update;
}

inline int ShadowSource::get_slot() const {
    return _slot;
}

inline void ShadowSource::set_slot(int slot) {
    _slot = slot;
}

inline void ShadowSource::set_pos_dir(LVecBase3f pos, LVecBase3f direction) {
    LQuaternion q;
    look_at(q, direction);
    LVecBase3f scale(1);
    LVecBase3f shear(0);
    compose_matrix(_transform, scale, shear, q.get_hpr(), pos);
    invalidate();
}
