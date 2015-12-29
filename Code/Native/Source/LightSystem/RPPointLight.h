#ifndef RP_POINT_LIGHT_H
#define RP_POINT_LIGHT_H

#include "pandabase.h"
#include "RPLight.h"

/**
 * @brief PointLight class
 * @details This represents a point light, a light which has a position and
 *   radius. Checkout the RenderPipeline documentation for more information
 *   about this type of light.
 */
class RPPointLight : public RPLight {

    PUBLISHED:
        RPPointLight();
        ~RPPointLight();

        inline void set_radius(float radius);
        inline float get_radius() const;
        MAKE_PROPERTY(radius, get_radius, set_radius);

        inline void set_inner_radius(float inner_radius);
        inline float get_inner_radius() const;
        MAKE_PROPERTY(inner_radius, get_inner_radius, set_inner_radius);

    public:
        virtual void write_to_command(GPUCommand &cmd);
        virtual void update_shadow_sources();
        virtual void init_shadow_sources();
        
    protected:

        float _radius;
        float _inner_radius;

};

#include "RPPointLight.I"

#endif // RP_POINT_LIGHT_H
