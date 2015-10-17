


inline size_t GPUCommand::get_data_size() {
    return _data.size();    
}

inline void GPUCommand::push_int(int v) {
    _data.push_back((float)v);
}

inline void GPUCommand::push_float(float v) {
    _data.push_back(v);
}

inline void GPUCommand::push_vec3(const LVecBase3f &v) {
    _data.push_back(v.get_x());
    _data.push_back(v.get_y());
    _data.push_back(v.get_z());
}

inline void GPUCommand::push_vec4(const LVecBase4f &v) {
    _data.push_back(v.get_x());
    _data.push_back(v.get_y());
    _data.push_back(v.get_z());
    _data.push_back(v.get_w());
}

inline void GPUCommand::push_mat4(const LMatrix4f &v) {
    cerr << "ERROR: Not implemented: GPUCommand::push_mat4" << endl;
}