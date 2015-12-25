

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

inline void ShadowSource::set_perspective_lens(float fov, float near_plane, float far_plane, LVecBase3f pos, LVecBase3f direction) {
   
    // Construct the transformation matrix
    LMatrix4f transform_mat = LMatrix4f::translate_mat(-pos);

    cout << "transformation matrix is now " << transform_mat << endl;

    // Construct a temporary lens to generate the lens matrix
    PerspectiveLens temp_lens = PerspectiveLens(2 * fov, 2 * fov);
    temp_lens.set_film_offset(0, 0);
    temp_lens.set_near_far(near_plane, far_plane);
    temp_lens.set_view_vector(direction, LVector3::up());
    _mvp = transform_mat * temp_lens.get_projection_mat();
    invalidate();
}

inline void ShadowSource::on_update_done() {
    _needs_update = false;
}

inline bool ShadowSource::has_region() const {
    return _region.get_x() >= 0 && _region.get_y() >= 0 && _region.get_z() >= 0 && _region.get_w() >= 0;
}

inline size_t ShadowSource::get_resolution() const {
    return _resolution;
}

inline const LVecBase4i& ShadowSource::get_region() const {
    return _region;
}

inline void ShadowSource::set_region(LVecBase4i region) {
    _region = region;
}


inline const LMatrix4f& ShadowSource::get_mvp() const {
    return _mvp;
}
