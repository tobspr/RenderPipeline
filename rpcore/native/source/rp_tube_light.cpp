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


#include "rp_tube_light.h"

#define _USE_MATH_DEFINES
#include <math.h>

/**
 * @brief Constructs a new tube light
 * @details This contructs a new tube light with default settings.
 */
RPTubeLight::RPTubeLight() :
    RPLight(RPLight::LT_tube_light), 
    _tube_radius(0.5),
    _tube_length(4),
    _tube_direction(1, 0, 0) {
}

/**
 * @brief Writes the light to a GPUCommand
 * @details This writes the light data to a GPUCommand.
 * @see RPLight::write_to_command
 *
 * @param cmd The target GPUCommand
 */
void RPTubeLight::write_to_command(GPUCommand &cmd) {
    RPLight::write_to_command(cmd);
    cmd.push_float(_tube_radius);
    cmd.push_float(_tube_length);
    cmd.push_vec3(_tube_direction);
}

/**
 * @brief Inits the shadow sources of the light
 * @details This inits all required shadow sources for the sphere light.
 * @see RPLight::init_shadow_sources
 */
void RPTubeLight::init_shadow_sources() {
    nassertv(_shadow_sources.size() == 0);
    std::cout << "Tube lights do not support shadows yet!" << std::endl;
    nassertv(false); // Shadows not supported yet
}

/**
 * @brief Updates the shadow sources
 * @details This updates all shadow sources of the light.
 * @see RPLight::update_shadow_sources
 */
void RPTubeLight::update_shadow_sources() {
    
    std::cout << "Tube lights do not support shadows yet!" << std::endl;
    nassertv(false);
}


/**
 * @brief See RPLight::get_conversion_factor
 */
float RPTubeLight::get_conversion_factor(IntensityType from, IntensityType to) const {
    if (from == to) 
        return 1.0;

    float divisor = M_PI * (2.0 * M_PI * _tube_radius * _tube_length + 4.0 * M_PI * _tube_radius * _tube_radius);
    if (from == IT_luminance && to == IT_lumens)
        return divisor;
    else if(from == IT_lumens && to == IT_luminance)
        return 1.0 / divisor;

    nassertr_always(false, 0.0);
    return 0.0;
}

