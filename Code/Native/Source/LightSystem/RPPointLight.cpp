
#include "RPPointLight.h"


/**
 * @brief Constructs a new point light
 * @details This contructs a new point light with default settings. By default
 *   the light is set to be an infinitely small point light source. You can
 *   change this with RPPointLight::set_inner_radius.   
 */
RPPointLight::RPPointLight() : RPLight(RPLight::LT_point_light) {
    _radius = 10.0;
    _inner_radius = 0.0;
}

/**
 * @brief Writes the light to a GPUCommand
 * @details This writes the point light data to a GPUCommand.
 * @see RPLight::write_to_command
 * 
 * @param cmd The target GPUCommand
 */
void RPPointLight::write_to_command(GPUCommand &cmd) {
    RPLight::write_to_command(cmd);
    cmd.push_float(_radius);
    cmd.push_float(_inner_radius);    
}

/**
 * @brief Inits the shadow sources of the light
 * @details This inits all required shadow sources for the point light.
 * @see RPLight::init_shadow_sources
 */
void RPPointLight::init_shadow_sources() {
    nassertv(_shadow_sources.size() == 0);
    // TODO
}

/**
 * @brief Updates the shadow sources
 * @details This updates all shadow sources of the light.
 * @see RPLight::update_shadow_sources
 */
void RPPointLight::update_shadow_sources() {
    // TODO
}
