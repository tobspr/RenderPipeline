

inline void Light::mark_dirty() {
    _dirty = true;
}

inline void Light::set_position(const LVecBase3f &pos) {
    set_position(pos.get_x(), pos.get_y(), pos.get_z());
}

inline void Light::set_position(float x, float y, float z) {
    _position.set(x, y, z);
    mark_dirty();
}


inline void Light::set_color(const LVecBase3f &color) {
    set_color(color.get_x(), color.get_y(), color.get_z());
}

inline void Light::set_color(float r, float g, float b) {
    _color.set(r, g, b);
    mark_dirty();
}

inline bool Light::has_slot() {
    return _slot >= 0;
}

inline void Light::remove_slot() {
    _slot = -1;
}

inline void Light::assign_slot(int slot) {
    _slot = slot;
}

inline Light::LightType Light::get_light_type() {
    return _light_type;
}