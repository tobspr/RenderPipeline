
inline void RPPointLight::set_radius(float radius) {
    _radius = radius;
    set_needs_update(true);
    invalidate_shadows();
}

inline float RPPointLight::get_radius() const {
    return _radius;
}

inline void RPPointLight::set_inner_radius(float inner_radius) {
    _inner_radius = inner_radius;
    set_needs_update(true);
}

inline float RPPointLight::get_inner_radius() const {
    return _inner_radius;
}
