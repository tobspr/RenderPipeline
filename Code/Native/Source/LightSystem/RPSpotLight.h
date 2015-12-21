
#ifndef RP_SPOT_LIGHT_H
#define RP_SPOT_LIGHT_H


#include "pandabase.h"
#include "RPLight.h"


class RPSpotLight : public RPLight {

    PUBLISHED:
        RPSpotLight();
        ~RPSpotLight();

        inline void set_radius(float radius);
        inline void set_fov(float fov);

        inline void set_direction(LVecBase3f direction);
        inline void set_direction(float dx, float dy, float dz);

        inline void look_at(LVecBase3f point);
        inline void look_at(float x, float y, float z);

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