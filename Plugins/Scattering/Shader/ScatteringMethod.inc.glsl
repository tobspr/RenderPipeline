#pragma once

#pragma include "Includes/Configuration.inc.glsl"

// This file just includes the scattering kernel based on the selected scattering
// method


#if ENUM_V_ACTIVE(Scattering, scattering_method, eric_bruneton)
    #pragma include "eric_bruneton/compute_scattering.inc.glsl"
#elif ENUM_V_ACTIVE(Scattering, scattering_method, hosek_wilkie)
    #pragma include "hosek_wilkie/compute_scattering.inc.glsl"
#else
    #error Unkown Scattering Method!
#endif

