

inline void RPSpotLight::set_radius(float radius) {
    _radius = radius;
    mark_dirty();
}


inline void RPSpotLight::set_fov(float fov) {
    _fov = fov;
    mark_dirty();
}

inline void RPSpotLight::set_direction(LVecBase3f direction) {
    _direction = direction;
    _direction.normalize();
    mark_dirty();
}

inline void RPSpotLight::set_direction(float dx, float dy, float dz) {
    _direction.set(dx, dy, dz);
    _direction.normalize();
    mark_dirty();
}

inline void RPSpotLight::look_at(LVecBase3f point) {
    set_direction(point - _position);
}

inline void RPSpotLight::look_at(float x, float y, float z) {
    set_direction(LVecBase3f(x, y, z) - _position);
}
