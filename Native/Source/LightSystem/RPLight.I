

inline void RPLight::mark_dirty() {
    _dirty = true;
}

inline void RPLight::unset_dirty_flag() {
    _dirty = false;
}

inline bool RPLight::is_dirty() {
    return _dirty;
}

inline void RPLight::set_pos(const LVecBase3f &pos) {
    set_pos(pos.get_x(), pos.get_y(), pos.get_z());
}

inline void RPLight::set_pos(float x, float y, float z) {
    _position.set(x, y, z);
    mark_dirty();
}

inline void RPLight::set_color(const LVecBase3f &color) {
    set_color(color.get_x(), color.get_y(), color.get_z());
}

inline void RPLight::set_color(float r, float g, float b) {
    _color.set(r, g, b);
    mark_dirty();
}

inline bool RPLight::has_slot() {
    return _slot >= 0;
}

inline void RPLight::remove_slot() {
    _slot = -1;
}

inline void RPLight::assign_slot(int slot) {
    _slot = slot;
}

inline RPLight::LightType RPLight::get_light_type() {
    return _light_type;
}

inline int RPLight::get_slot() {
    return _slot;
}