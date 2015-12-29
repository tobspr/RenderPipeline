
#include "RPPointLight.h"


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

void RPPointLight::init_shadow_sources() {
    nassertv(_shadow_sources.size() == 0);
    // TODO
}

void RPPointLight::update_shadow_sources() {
    // TODO
}
