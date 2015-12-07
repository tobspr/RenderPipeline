
inline void GPUCommand::push_int(int v) {
    push_float((float)v);
}

inline void GPUCommand::push_float(float v) {
    if (_current_index >= 32) {
        cerr << "GPUCommand out of bounds!" << endl;
        return;
    }
    _data[_current_index++] = v;
}

inline void GPUCommand::push_vec3(const LVecBase3f &v) {
    push_float(v.get_x());
    push_float(v.get_y());
    push_float(v.get_z());
}

inline void GPUCommand::push_vec4(const LVecBase4f &v) {
    push_float(v.get_x());
    push_float(v.get_y());
    push_float(v.get_z());
    push_float(v.get_w());
}

inline void GPUCommand::push_mat4(const LMatrix4f &v) {
    cerr << "ERROR: Not implemented: GPUCommand::push_mat4" << endl;
}