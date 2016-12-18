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

#ifndef RP_TUBE_LIGHT
#define RP_TUBE_LIGHT

#include "pandabase.h"
#include "rp_light.h"

/**
 * @brief TubeLight class
 * @details This represents a tube light, a light which has a tube radius and length.
 *   Checkout the RenderPipeline documentation for more information
 *   about this type of light.
 */
class RPTubeLight : public RPLight {

    PUBLISHED:
        RPTubeLight();

        inline void set_tube_radius(float tube_radius);
        inline float get_tube_radius() const;
        MAKE_PROPERTY(tube_radius, get_tube_radius, set_tube_radius);

        inline void set_tube_length(float tube_length);
        inline float get_tube_length() const;
        MAKE_PROPERTY(tube_length, get_tube_length, set_tube_length);

        inline void set_tube_direction(const LVecBase3f& tube_direction);
        inline const LVecBase3f& get_tube_direction() const;
        MAKE_PROPERTY(tube_direction, get_tube_direction, set_tube_direction);

    public:
        virtual void write_to_command(GPUCommand &cmd);
        virtual void update_shadow_sources();
        virtual void init_shadow_sources();

    protected:

        virtual float get_conversion_factor(IntensityType from, IntensityType to) const;

        float _tube_radius;
        float _tube_length;
        LVecBase3f _tube_direction;
};

#include "rp_tube_light.I"

#endif // RP_TUBE_LIGHT
