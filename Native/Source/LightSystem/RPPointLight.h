
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

        virtual void write_to_command(GPUCommand &cmd);

    protected:

        float _radius;
        float _inner_radius;

};

#include "RPPointLight.I"

#endif // RP_POINT_LIGHT_H