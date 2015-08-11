

class LightLimits:

    """ This class stores the hardcoded maximum numbers of lights and shadowmaps.
    The maximum numbers depend on the maximum available uniform shader inputs,
    and may vary, but for now we hardcode this values. """

    maxLights = {
        "PointLight": 3,
        "PointLightShadow": 3,
        "DirectionalLight": 3,
        "DirectionalLightShadow": 3,
        "SpotLight": 3,
        "SpotLightShadow": 3,
        "GIHelperLightShadow": 3
    }

    maxPerTileLights = {
        "PointLight": 3,
        "PointLightShadow": 3,
        "DirectionalLight": 3,
        "DirectionalLightShadow": 3,
        "SpotLight": 3,
        "SpotLightShadow": 3,
    }

    maxTotalLights = 3
    maxShadowMaps = 7

