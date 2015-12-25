
/**
 * @brief Appends an integer to the GPUCommand.
 * @details This adds an integer to the back of the GPUCommand. Depending on the
 *   setting in convert_int_to_float, this will either just convert the int to a
 *   float by casting it, or just do a bitwise copy. 
 * 
 * @param v The integer to append.
 */
inline void GPUCommand::push_int(int v) {
    push_float(convert_int_to_float(v));
}

/**
 * @brief Internal method to convert an integer to float
 * @details This methods gets called by the GPUCommand::push_int, and manages
 *   storing an integer in a floating point variable. There are two options, 
 *   which are documented inside of the method. Just be sure to adjust the
 *   flag in the main shader configuration, too (see below.)
 * 
 * @param v Integer to convert
 * @return Float-representation of that integer, either casted or binary converted.s
 */
inline float GPUCommand::convert_int_to_float(int v) const {

    #if 0
        // Just round to float, can cause rounding issues tho
        // If you use this, set GPU_CMD_INT_AS_FLOAT to 0 in Shader/Includes/Configuration.inc.glsl
        return (float)v;
        
    #else
        // Store the int bits as float, and unpack it later in the shader
        // If you use this, set GPU_CMD_INT_AS_FLOAT to 1 in Shader/Includes/Configuration.inc.glsl
        union { int _int; float _float; } converter = { v };
        return converter._float;
    #endif
}

/**
 * @brief Appends a float to the GPUCommand.
 * @details This adds an integer to the back of the GPUCommand. Its used by all
 *   other push_xxx methods, and simply stores the value, then increments the write
 *   pointer. When the amount of floats exceeds the capacity of the GPUCommand,
 *   an error will be printed, and the method returns without doing anything else.
 * 
 * @param v The float to append.
 */
inline void GPUCommand::push_float(float v) {
    if (_current_index >= GPU_COMMAND_ENTRIES) {
        gpucommand_cat.error() << "Out of bounds! Exceeded command size of " << GPU_COMMAND_ENTRIES << endl;
        return;
    }
    _data[_current_index++] = v;
}

/**
 * @brief Appends a 3-component floating point vector to the GPUCommand.
 * @details This appends a 3-component floating point vector to the command.
 *   It basically just calls push_float() for every component, in the order
 *   x, y, z, which causes the vector to occupy the space of 3 floats. 
 * 
 * @param v Int-Vector to append.
 */
inline void GPUCommand::push_vec3(const LVecBase3f &v) {
    push_float(v.get_x());
    push_float(v.get_y());
    push_float(v.get_z());
}


/**
 * @brief Appends a 3-component integer vector to the GPUCommand.
 * @details This appends a 3-component integer vector to the command.
 *   It basically just calls push_int() for every component, in the order
 *   x, y, z, which causes the vector to occupy the space of 3 floats. 
 * 
 * @param v Int-Vector to append.
 */
inline void GPUCommand::push_vec3(const LVecBase3i &v) {
    push_int(v.get_x());
    push_int(v.get_y());
    push_int(v.get_z());
}

/**
 * @brief Appends a 4-component floating point vector to the GPUCommand.
 * @details This appends a 4-component floating point vector to the command.
 *   It basically just calls push_float() for every component, in the order
 *   x, y, z, which causes the vector to occupy the space of 3 floats. 
 * 
 * @param v Int-Vector to append.
 */
inline void GPUCommand::push_vec4(const LVecBase4f &v) {
    push_float(v.get_x());
    push_float(v.get_y());
    push_float(v.get_z());
    push_float(v.get_w());
}

/**
 * @brief Appends a 4-component integer vector to the GPUCommand.
 * @details This appends a 4-component integer vector to the command.
 *   It basically just calls push_int() for every component, in the order
 *   x, y, z, w, which causes the vector to occupy the space of 4 floats. 
 * 
 * @param v Int-Vector to append.
 */
inline void GPUCommand::push_vec4(const LVecBase4i &v) {
    push_int(v.get_x());
    push_int(v.get_y());
    push_int(v.get_z());
    push_int(v.get_w());
}

/**
 * @brief Appends a floating point 3x3 matrix to the GPUCommand.
 * @details This appends a floating point 3x3 matrix to the GPUCommand, by
 *   pushing all components in row-order to the command. This occupies a space of
 *   9 floats.
 * 
 * @param v [description]
 */
inline void GPUCommand::push_mat3(const LMatrix3f &v) {
    for (size_t i = 0; i < 3; ++i) {
        for (size_t j = 0; j < 3; ++j) {
            push_float(v.get_cell(i, j));
        }
    }
}

/**
 * @brief Appends a floating point 4x4 matrix to the GPUCommand.
 * @details This appends a floating point 4x4 matrix to the GPUCommand, by
 *   pushing all components in row-order to the command. This occupies a space of
 *   16 floats.
 * 
 * @param v [description]
 */
inline void GPUCommand::push_mat4(const LMatrix4f &v) {
    for (size_t i = 0; i < 4; ++i) {
        for (size_t j = 0; j < 4; ++j) {
            push_float(v.get_cell(i, j));
        }
    }
}
