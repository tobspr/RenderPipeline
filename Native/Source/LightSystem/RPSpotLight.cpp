
#include "RPSpotLight.h"


RPSpotLight::RPSpotLight() : RPLight(RPLight::LT_spot_light) {
    _radius = 10.0;
    _fov = 45.0;
    _direction.set(0, 1, 0);
}

RPSpotLight::~RPSpotLight() {
}

void RPSpotLight::write_to_command(GPUCommand &cmd) {
    RPLight::write_to_command(cmd);
    cmd.push_float(_radius);
    cmd.push_float(_fov);    
    cmd.push_vec3(_direction);    
}
