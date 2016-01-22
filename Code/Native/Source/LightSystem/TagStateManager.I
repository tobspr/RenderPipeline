/**
 * 
 * RenderPipeline
 * 
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */


/**
 * @brief Returns the bitmask used for rendering the default scene geometry.
 * @details This returns the bitmask which will be used for normal rendering.
 * @return Default bitmask
 */
inline BitMask32 TagStateManager::get_gbuffer_mask() {
    return BitMask32::bit(1);
}

/**
 * @brief Returns the bitmask used for rendering shadows.
 * @details This returns the bitmask which will be used whenever rendering
 *   shadows, e.g. PSSM or regular shadow rendering.
 * @return Shadow bitmask
 */
inline BitMask32 TagStateManager::get_shadow_mask() {
    return BitMask32::bit(2);
}

/**
 * @brief Returns the bitmask used for voxelization.
 * @details This returns the bitmask which will be used when voxelizing the scene.
 *   This is for example used for the Global Illumination.
 * @return Voxelize bitmask
 */
inline BitMask32 TagStateManager::get_voxelize_mask() {
    return BitMask32::bit(3);
}

/**
 * @brief Registers a new camera which renders shadows
 * @details This registers a new camera which will be used to render shadows
 *   somewhere else. The TagStateManager will keep track of the camera and
 *   applies all registered states onto the camera with Camera::set_tag_state.
 *   It also applies the shadow camera mask (TagStateManager::get_shadow_mask)
 *   to the camera, and sets an initial state to disable color write.
 * 
 * @param source Camera which will be used to render shadows
 */
inline void TagStateManager::register_shadow_camera(Camera* source) {
    register_camera(_shadow_container, source);
}


/**
 * @brief Unregisters a camera from the list of shadow cameras
 * @details This unregisters a camera from the list of shadows cameras. It also
 *   resets all tag states of the camera, and also its initial state.
 * 
 * @param source Camera to unregister
 */
inline void TagStateManager::unregister_shadow_camera(Camera* source) {
    unregister_camera(_shadow_container, source);
}

/**
 * @brief Registers a new camera for voxelization
 * @details This registers a new camera which will be used to voxelize the scene
 *   somewhere else. The TagStateManager will keep track of the camera and
 *   applies all registered states onto the camera with Camera::set_tag_state.
 *   It also applies the voxelize camera mask (TagStateManager::get_voxelize_mask)
 *   to the camera, and sets an initial state to disable color write.
 * 
 * @param source Camera which will be used to render shadows
 */
inline void TagStateManager::register_voxelize_camera(Camera* source) {
    register_camera(_voxelize_container, source);
}


/**
 * @brief Unregisters a camera from the list of voxelization cameras
 * @details This unregisters a camera from the list of voxelization cameras. It also
 *   resets all tag states of the camera, and also its initial state.
 * 
 * @param source Camera to unregister
 */
inline void TagStateManager::unregister_voxelize_camera(Camera* source) {
    unregister_camera(_voxelize_container, source);
}


/**
 * @brief Applies a given shadow state to a NodePath
 * @details This applies a shader to the given NodePath which is used when the
 *   NodePath is rendered by any registered shadow camera to render shadows.
 *   It also disables color write (since its not required for shadows).
 *  
 * @param np The nodepath to apply the shader to
 * @param shader A handle to the shader to apply
 * @param name Name of the state, should be a unique identifier
 * @param sort Determines the sort with which the shader will be applied.
 */
inline void TagStateManager::apply_shadow_state(NodePath np, Shader* shader,
                                                const string &name, int sort) {
    apply_state(_shadow_container, np, shader, name, sort);
}

/**
 * @brief Applies a given voxelize state to a NodePath
 * @details This applies a shader to the given NodePath which is used when the
 *   NodePath is rendered by any registered voxelization camera to voxelize the
 *   scene. It also disables color write (since its not required for voxelization).
 *  
 * @param np The nodepath to apply the shader to
 * @param shader A handle to the shader to apply
 * @param name Name of the state, should be a unique identifier
 * @param sort Determines the sort with which the shader will be applied.
 */
inline void TagStateManager::apply_voxelize_state(NodePath np, Shader* shader,
                                                  const string &name, int sort) {
    apply_state(_voxelize_container, np, shader, name, sort);
}
