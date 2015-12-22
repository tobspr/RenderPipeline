

inline void RPLight::mark_dirty() {
    _dirty = true;
}

inline void RPLight::unset_dirty_flag() {
    _dirty = false;
}

inline bool RPLight::is_dirty() const {
    return _dirty;
}

inline void RPLight::set_pos(const LVecBase3f &pos) {
    set_pos(pos.get_x(), pos.get_y(), pos.get_z());
}

inline void RPLight::set_pos(float x, float y, float z) {
    _position.set(x, y, z);
    mark_dirty();
    invalidate_shadows();
}

inline void RPLight::set_color(const LVecBase3f &color) {
    set_color(color.get_x(), color.get_y(), color.get_z());
}

inline void RPLight::set_color(float r, float g, float b) {
    _color.set(r, g, b);
    mark_dirty();
}

inline bool RPLight::has_slot() const {
    return _slot >= 0;
}

inline void RPLight::remove_slot() {
    _slot = -1;
}

inline void RPLight::assign_slot(int slot) {
    _slot = slot;
}

inline RPLight::LightType RPLight::get_light_type() const {
    return _light_type;
}

inline int RPLight::get_slot() const {
    return _slot;
}

inline void RPLight::set_ies_profile(int profile) {
    _ies_profile = profile;
}

inline void RPLight::set_casts_shadows(bool flag) {
    if (has_slot()) {
        cerr << "Light is already attached, can not call set_casts_shadows!" << endl;
        return;
    }
    _casts_shadows = flag;
}

inline bool RPLight::get_casts_shadows() const {
    return _casts_shadows;
}

inline int RPLight::get_num_shadow_sources() const {
    return _shadow_sources.size();
}

inline ShadowSource* RPLight::get_shadow_source(int index) const {
    nassertr(index < _shadow_sources.size(), NULL);
    return _shadow_sources[index];
}

inline void RPLight::invalidate_shadows() {
    for (size_t i = 0; i < _shadow_sources.size(); ++i) {
        _shadow_sources[i]->invalidate();
    }
}

