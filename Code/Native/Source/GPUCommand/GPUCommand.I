
inline void GPUCommand::push_int(int v) {
    push_float(convert_int_to_float(v));
}

inline float GPUCommand::convert_int_to_float(int v) const {

    #if 0
        // Just round to float, can cause rounding issues tho
        // If you use this, set GPU_CMD_INT_AS_FLOAT to 0 in Shader/Includes/Configuration.inc.glsl
        return (float)v;
        
    #else
        // Store the int bits as float, and unpack it later in the shader
        // If you use this, set GPU_CMD_INT_AS_FLOAT to 1 in Shader/Includes/Configuration.inc.glsl
        union int2float {
            int _int;
            float _float;
        };
        int2float converter;
        converter._int = v;
        return converter._float;
    #endif
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
    for (size_t i = 0; i < 4; ++i) {
        for (size_t j = 0; j < 4; ++j) {
            push_float(v.get_cell(i, j));
        }
    }
}
