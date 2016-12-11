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

#ifndef RP_LIGHT_H
#define RP_LIGHT_H

#include "referenceCount.h"
#include "luse.h"
#include "gpu_command.h"
#include "shadow_source.h"

/**
 * @brief Base class for Lights
 * @details This is the base class for all lights in the render pipeline. It
 *   stores common properties, and provides methods to modify these.
 *   It also defines some interface functions which subclasses have to implement.
 */
class RPLight : public ReferenceCount {

    PUBLISHED:

        /**
         * Different types of light.
         */
        enum LightType {
            LT_empty = 0,
            LT_sphere_light = 1,
            LT_spot_light = 2,
        };

        enum IntensityType {
            IT_lumens = 0,   // Intensity in lumens, does not depend on emitter size
            IT_luminance = 1 // Intensity in cd/m^2, does depend on emitter size
        };

    public:
        RPLight(LightType light_type);
        virtual ~RPLight();

        virtual void init_shadow_sources() = 0;
        virtual void update_shadow_sources() = 0;
        virtual void write_to_command(GPUCommand &cmd);

        inline int get_num_shadow_sources() const;
        inline ShadowSource* get_shadow_source(size_t index) const;
        inline void clear_shadow_sources();

        inline void set_needs_update(bool flag);
        inline bool get_needs_update() const;

        inline bool has_slot() const;
        inline int get_slot() const;
        inline void remove_slot();
        inline void assign_slot(int slot);

        inline void invalidate_shadows();

    PUBLISHED:

        inline void set_pos(const LVecBase3f &pos);
        inline void set_pos(float x, float y, float z);
        inline const LVecBase3f& get_pos() const;
        MAKE_PROPERTY(pos, get_pos, set_pos);

        inline void set_color(const LVecBase3f &color);
        inline void set_color(float r, float g, float b);
        inline const LVecBase3f& get_color() const;
        MAKE_PROPERTY(color, get_color, set_color);

        void set_color_from_temperature(float temperature);

        inline void set_intensity_lumens(float intensity_lumens);
        inline float get_intensity_lumens() const;
        MAKE_PROPERTY(intensity_lumens, get_intensity_lumens, set_intensity_lumens);

        inline void set_intensity_luminance(float intensity_luminance);
        inline float get_intensity_luminance() const;
        MAKE_PROPERTY(intensity_luminance, get_intensity_luminance, set_intensity_luminance);


        inline LightType get_light_type() const;
        MAKE_PROPERTY(light_type, get_light_type);

        inline void set_casts_shadows(bool flag = true);
        inline bool get_casts_shadows() const;
        MAKE_PROPERTY(casts_shadows, get_casts_shadows, set_casts_shadows);

        inline void set_shadow_map_resolution(size_t resolution);
        inline size_t get_shadow_map_resolution() const;
        MAKE_PROPERTY(shadow_map_resolution, get_shadow_map_resolution, set_shadow_map_resolution);

        inline void set_ies_profile(int profile);
        inline int get_ies_profile() const;
        inline bool has_ies_profile() const;
        inline void clear_ies_profile();
        MAKE_PROPERTY2(ies_profile, has_ies_profile, get_ies_profile,
                                    set_ies_profile, clear_ies_profile);

        inline void set_near_plane(float near_plane);
        inline float get_near_plane() const;
        MAKE_PROPERTY(near_plane, get_near_plane, set_near_plane);

        inline void set_max_cull_distance(float max_cull_distance);
        inline float get_max_cull_distance() const;
        MAKE_PROPERTY(max_cull_distance, get_max_cull_distance, set_max_cull_distance);


    protected:

        // used to convert between luminance and luminous power
        virtual float get_conversion_factor(IntensityType from, IntensityType to) const = 0;
 
        int _slot;
        int _ies_profile;
        size_t _source_resolution;
        bool _needs_update;
        bool _casts_shadows;
        LVecBase3f _position;
        LVecBase3f _color;
        LightType _light_type;
        float _near_plane;

        float _intensity;
        IntensityType _intensity_type;

        float _max_cull_distance;

        vector<ShadowSource*> _shadow_sources;
};

#include "rp_light.I"

#endif // RP_LIGHT_H
