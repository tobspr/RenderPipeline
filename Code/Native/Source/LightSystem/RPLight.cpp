/**
 * 
 * RenderPipeline
 * 
 * Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>
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


#include "RPLight.h"


/**
 * @brief Constructs a new light with the given type
 * @details This constructs a new base light with the given light type.
 *   Sub-Classes should call this to initialize all properties.
 * 
 * @param light_type Type of the light
 */
RPLight::RPLight(LightType light_type) {
    _light_type = light_type;
    _needs_update = false;
    _casts_shadows = false;
    _slot = -1;
    _position.set(0, 0, 0);
    _color.set(1, 1, 1);
    _ies_profile = -1;
    _source_resolution = 512;
    _near_plane = 0.1;
    _lumens = 20.0;
}

/**
 * @brief Writes the light to a GPUCommand
 * @details This writes all of the lights data to the given GPUCommand handle.
 *   Subclasses should first call this method, and then append their own
 *   data. This makes sure that for unpacking a light, no information about
 *   the type of the light is required.
 * 
 * @param cmd The GPUCommand to write to
 */
void RPLight::write_to_command(GPUCommand &cmd) {
    cmd.push_int(_light_type);
    cmd.push_int(_ies_profile);

    if (_casts_shadows) {
        // If we casts shadows, write the index of the first source, we expect
        // them to be consecutive
        nassertv(_shadow_sources.size() >= 0);
        nassertv(_shadow_sources[0]->has_slot());
        cmd.push_int(_shadow_sources[0]->get_slot());
    } else {
        // If we cast no shadows, just push a negative number
        cmd.push_int(-1);
    }

    cmd.push_vec3(_position);

    // Get the lights color by multiplying color with lumens, I hope thats
    // physically correct.
    cmd.push_vec3(_color * _lumens);
}

/**
 * @brief Light destructor
 * @details This destructs the light, cleaning up all resourced used. The light
 *   should be detached at this point, because while the Light is attached,
 *   the InternalLightManager holds a reference to prevent it from being
 *   destructed. 
 */
RPLight::~RPLight() {
    nassertv(!has_slot()); // Light still attached - should never happen
    clear_shadow_sources();
}
