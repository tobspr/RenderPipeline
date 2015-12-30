#ifndef RP_SPOT_LIGHT_H
#define RP_SPOT_LIGHT_H

#include "pandabase.h"
#include "RPLight.h"

/**
 * @brief SpotLight class
 * @details This represents a spot light, a light which has a position, radius,
 *   direction and FoV. Checkout the RenderPipeline documentation for more
 *   information about this type of light.
 */
class RPSpotLight : public RPLight {

    PUBLISHED:
        RPSpotLight();

        inline void set_radius(float radius);
        inline float get_radius() const;
        MAKE_PROPERTY(radius, get_radius, set_radius);        

        inline void set_fov(float fov);
        inline float get_fov() const;
        MAKE_PROPERTY(fov, get_fov, set_fov);

        inline void set_direction(LVecBase3f direction);
        inline void set_direction(float dx, float dy, float dz);
        inline const LVecBase3f& get_direction() const;
        inline void look_at(LVecBase3f point);
        inline void look_at(float x, float y, float z);
        MAKE_PROPERTY(direction, get_direction, set_direction);

    public:
        virtual void write_to_command(GPUCommand &cmd);
        virtual void init_shadow_sources();
        virtual void update_shadow_sources();

    protected:
        float _radius;
        float _fov;
        LVecBase3f _direction;
};

#include "RPSpotLight.I"

#endif // RP_SPOT_LIGHT_H
