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
 * @brief Sets the up vector of the light
 */
inline void RPRectangleLight::set_up_vector(const LVecBase3f& up_vector) {
    nassertv(up_vector.length() >= 0.0099); // Invalid size
    _up_vector = up_vector;
    set_needs_update(true);
}

/**
 * @brief Returns the up vector of the light
 */
inline const LVecBase3f& RPRectangleLight::get_up_vector() const {
    return _up_vector;
}

/**
 * @brief Sets the right vector of the light
 */
inline void RPRectangleLight::set_right_vector(const LVecBase3f& right_vector) {
    nassertv(right_vector.length() >= 0.0099); // Invalid size
    _right_vector = right_vector;
    set_needs_update(true);
}

/**
 * @brief Returns the right vector of the light
 */
inline const LVecBase3f& RPRectangleLight::get_right_vector() const {
    return _right_vector;
}
