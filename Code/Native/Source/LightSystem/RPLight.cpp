
#include "RPLight.h"


RPLight::RPLight(LightType light_type) {
    _light_type = light_type;
    _dirty = false;
    _casts_shadows = false;
    _slot = -1;
    _position.set(0, 0, 0);
    _color.set(1, 1, 1);
    _ies_profile = -1;
    _source_resolution = 512;
    _near_plane = 0.1;
}


void RPLight::write_to_command(GPUCommand &cmd) {

    cmd.push_int(_light_type);
    cmd.push_int(_ies_profile);

    if (_casts_shadows) {
        // If we casts shadows, write the index of the first source, we expect
        // them to be consecutive
        nassertv(_shadow_sources.size() >= 0);
        nassertv(_shadow_sources[0]->has_slot());
        cmd.push_int(_shadow_sources[0]->get_slot());
    } else {
        // If we cast no shadows, just push a negative number
        cmd.push_int(-1);
    }

    cmd.push_vec3(_position);
    cmd.push_vec3(_color);
}


RPLight::~RPLight() {
    // Default dtor, for now
}

