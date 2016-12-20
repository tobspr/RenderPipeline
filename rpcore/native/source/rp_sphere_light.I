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
 * @brief Sets the sphere size of the light
 * @details This sets the sphere size of the light. This has influence on the
 *   specular highlights of the light aswell as the shadows.
 *
 *   The sphere size controls the size of the lights sphere size in world
 *   space units, and impacts the specular highlight. In case the intensity
 *   was specified in luminance, this also affects the intensity of the light.
 *
 * @param sphere-size Sphere size in world space
 */
inline void RPSphereLight::set_sphere_radius(float sphere_radius) {
    nassertv(sphere_radius >= 0.0099); // Invalid size
    _sphere_radius = sphere_radius;
    set_needs_update(true);
}

/**
 * @brief Returns the sphere size of the light
 * @details This returns the sphere size of the light, previously set with
 *   RPSphereLight::set_sphere_radius.
 * @return sphere size in world space units
 */
inline float RPSphereLight::get_sphere_radius() const {
    return _sphere_radius;
}
