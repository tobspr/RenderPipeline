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
 * @brief Sets the Field of View in degrees
 */
inline void RPSpotLight::set_fov(float fov) {
    _fov = fov;
    set_needs_update(true);
    invalidate_shadows();
}

/**
 * @brief Returns the ield of view in degrees
 */
inline float RPSpotLight::get_fov() const {
    return _fov;
}


/**
 * @brief Sets the direction of the spot light
 */
inline void RPSpotLight::set_direction(LVecBase3f direction) {
    _direction = direction;
    _direction.normalize();
    set_needs_update(true);
    invalidate_shadows();
}


/**
 * @brief Sets the direction of the spot light
 */
inline void RPSpotLight::set_direction(float dx, float dy, float dz) {
    _direction.set(dx, dy, dz);
    _direction.normalize();
    set_needs_update(true);
    invalidate_shadows();
}


/**
 * @brief Returns the direction of the spot light
 */
inline const LVecBase3f& RPSpotLight::get_direction() const {
    return _direction;
}


/**
 * @brief Sets the direction of the spot light by facing it towards a given point
 */
inline void RPSpotLight::look_at(LVecBase3f point) {
    set_direction(point - _position);
}


/**
 * @brief Sets the direction of the spot light by facing it towards a given point
 */
inline void RPSpotLight::look_at(float x, float y, float z) {
    set_direction(LVecBase3f(x, y, z) - _position);
}
