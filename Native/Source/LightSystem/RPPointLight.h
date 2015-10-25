
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

    public:
      static TypeHandle get_class_type() {
        return _type_handle;
      }
      static void init_type() {
        RPLight::init_type();
        register_type(_type_handle, "RPPointLight",
                      RPLight::get_class_type());
      }
      virtual TypeHandle get_type() const {
        return get_class_type();
      }

    private:
      static TypeHandle _type_handle;


};

#include "RPPointLight.I"

#endif // RP_POINT_LIGHT_H