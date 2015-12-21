
#ifndef RP_POINT_LIGHT_H
#define RP_POINT_LIGHT_H


#include "pandabase.h"
#include "RPLight.h"


class RPPointLight : public RPLight {

    PUBLISHED:
        RPPointLight();
        ~RPPointLight();

        inline void set_radius(float radius);
        inline void set_inner_radius(float inner_radius);

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
