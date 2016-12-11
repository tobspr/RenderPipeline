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


#include "rp_sphere_light.h"

#define _USE_MATH_DEFINES
#include <math.h>

/**
 * @brief Constructs a new sphere light
 * @details This contructs a new sphere light with default settings.
 */
RPSphereLight::RPSphereLight() :
    RPLight(RPLight::LT_sphere_light),
    _sphere_size(0.2) {
}

/**
 * @brief Writes the light to a GPUCommand
 * @details This writes the sphere light data to a GPUCommand.
 * @see RPLight::write_to_command
 *
 * @param cmd The target GPUCommand
 */
void RPSphereLight::write_to_command(GPUCommand &cmd) {
    RPLight::write_to_command(cmd);
    cmd.push_float(_sphere_size);
}

/**
 * @brief Inits the shadow sources of the light
 * @details This inits all required shadow sources for the sphere light.
 * @see RPLight::init_shadow_sources
 */
void RPSphereLight::init_shadow_sources() {
    nassertv(_shadow_sources.size() == 0);
    // Create 6 shadow sources, one for each direction
    for(size_t i = 0; i < 6; ++i) {
        _shadow_sources.push_back(new ShadowSource());
    }
}

/**
 * @brief Updates the shadow sources
 * @details This updates all shadow sources of the light.
 * @see RPLight::update_shadow_sources
 */
void RPSphereLight::update_shadow_sources() {
    LVecBase3f directions[6] = {
        LVecBase3f( 1,  0,  0),
        LVecBase3f(-1,  0,  0),
        LVecBase3f( 0,  1,  0),
        LVecBase3f( 0, -1,  0),
        LVecBase3f( 0,  0,  1),
        LVecBase3f( 0,  0, -1)
    };

    // Increase fov to prevent artifacts at the shadow map transitions
    const float fov = 90.0f + 3.0f;
    for (size_t i = 0; i < _shadow_sources.size(); ++i) {
        _shadow_sources[i]->set_resolution(get_shadow_map_resolution());
        _shadow_sources[i]->set_perspective_lens(fov, _near_plane, _max_cull_distance,
                                                _position, directions[i]);
    }
}


/**
 * @brief See RPLight::get_conversion_factor
 */
float RPSphereLight::get_conversion_factor(IntensityType from, IntensityType to) const {
    if (from == to) 
        return 1.0;

    float divisor = 4.0 * _sphere_size * _sphere_size * M_PI * M_PI;
    if (from == IT_luminance && to == IT_lumens)
        return divisor;
    else if(from == IT_lumens && to == IT_luminance)
        return 1.0 / divisor;

    nassertr_always(false, 0.0);
    return 0.0;
}
