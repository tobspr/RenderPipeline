
#include "RPPointLight.h"


// TypeHandle RPPointLight::_type_handle;



RPPointLight::RPPointLight() : RPLight(RPLight::LT_point_light) {
    _radius = 10.0;
    _inner_radius = 0.0;
}

RPPointLight::~RPPointLight() {

}

void RPPointLight::write_to_command(GPUCommand &cmd) {
    RPLight::write_to_command(cmd);
    cmd.push_float(_radius);
    cmd.push_float(_inner_radius);    
}
