
inline void RPPointLight::set_radius(float radius) {
    _radius = radius;
    mark_dirty();
}

inline void RPPointLight::set_inner_radius(float inner_radius) {
    _inner_radius = inner_radius;
    mark_dirty();
}
