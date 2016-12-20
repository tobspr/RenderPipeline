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

#ifndef RP_RECTANGLE_LIGHT
#define RP_RECTANGLE_LIGHT

#include "pandabase.h"
#include "rp_light.h"

/**
 * @brief RectangleLight class
 * @details This represents a rectangle light, a light which is on a limited plane.
 *   Checkout the RenderPipeline documentation for more information
 *   about this type of light.
 */
class RPRectangleLight : public RPLight {

    PUBLISHED:
        RPRectangleLight();

        inline void set_up_vector(const LVecBase3f& up_vector);
        inline const LVecBase3f& get_up_vector() const;
        MAKE_PROPERTY(up_vector, get_up_vector, set_up_vector);

        inline void set_right_vector(const LVecBase3f& right_vector);
        inline const LVecBase3f& get_right_vector() const;
        MAKE_PROPERTY(right_vector, get_right_vector, set_right_vector);


    public:
        virtual void write_to_command(GPUCommand &cmd);
        virtual void update_shadow_sources();
        virtual void init_shadow_sources();

    protected:

        virtual float get_conversion_factor(IntensityType from, IntensityType to) const;

        LVecBase3f _up_vector;
        LVecBase3f _right_vector;
};

#include "rp_rectangle_light.I"

#endif // RP_RECTANGLE_LIGHT
