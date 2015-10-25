
#include "PointLight.h"


PointLight::PointLight() : Light(Light::LT_point_light) {
    _radius = 10.0;
    _inner_radius = 0.0;
}

PointLight::~PointLight() {

}

void PointLight::write_to_command(GPUCommand &cmd) {
    Light::write_to_command(cmd);
    cmd.push_float(_radius);
    cmd.push_float(_inner_radius);    
}