
#include "RPLight.h"

// TypeHandle RPLight::_type_handle;

RPLight::RPLight(LightType light_type) {
    _light_type = light_type;
    _dirty = false;
    _slot = -1;
    _position.set(0, 0, 0);
    _color.set(1, 1, 1);
}


void RPLight::write_to_command(GPUCommand &cmd) {
    cmd.push_int(_slot);
    cmd.push_int(_light_type);
    cmd.push_vec3(_position);
    cmd.push_vec3(_color);
}

