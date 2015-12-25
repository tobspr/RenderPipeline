
#include "RPSpotLight.h"

#define _USE_MATH_DEFINES
#include <math.h>


RPSpotLight::RPSpotLight() : RPLight(RPLight::LT_spot_light) {
    _radius = 10.0;
    _fov = 45.0;
    _direction.set(0, 0, -1);
}

RPSpotLight::~RPSpotLight() {
}

void RPSpotLight::write_to_command(GPUCommand &cmd) {
    RPLight::write_to_command(cmd);
    cmd.push_float(_radius);

    // Convert FOV to 0 .. PI
    cmd.push_float(_fov / 180.0 * M_PI);
    cmd.push_vec3(_direction);
}


void RPSpotLight::init_shadow_sources() {
    nassertv(_shadow_sources.size() == 0);
    ShadowSource* main_source = new ShadowSource();
    _shadow_sources.push_back(main_source);
}

void RPSpotLight::update_shadow_sources() {
    cout << "updating shadow sources .." << endl;
    _shadow_sources[0]->set_perspective_lens(_fov, 0.3, _radius, _position, _direction);
}

