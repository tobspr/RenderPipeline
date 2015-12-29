

inline void RPSpotLight::set_radius(float radius) {
    _radius = radius;
    set_needs_update(true);
    invalidate_shadows();
}

inline float RPSpotLight::get_radius() const {
    return _radius;
}


inline void RPSpotLight::set_fov(float fov) {
    _fov = fov;
    set_needs_update(true);
    invalidate_shadows();
}

inline float RPSpotLight::get_fov() const {
    return _fov;
}

inline void RPSpotLight::set_direction(LVecBase3f direction) {
    _direction = direction;
    _direction.normalize();
    set_needs_update(true);
    invalidate_shadows();
}

inline void RPSpotLight::set_direction(float dx, float dy, float dz) {
    _direction.set(dx, dy, dz);
    _direction.normalize();
    set_needs_update(true);
    invalidate_shadows();
}

inline const LVecBase3f& RPSpotLight::get_direction() const {
    return _direction;
}

inline void RPSpotLight::look_at(LVecBase3f point) {
    set_direction(point - _position);
}

inline void RPSpotLight::look_at(float x, float y, float z) {
    set_direction(LVecBase3f(x, y, z) - _position);
}
