

class LightLimits:

    """ This class stores the hardcoded maximum numbers of lights and shadowmaps.
    The maximum numbers depend on the maximum available uniform shader inputs,
    and may vary, but for now we hardcode this values. """

    maxLights = {
        "PointLight": 3,
        "PointLightShadow": 5,
        "DirectionalLight": 3,
        "DirectionalLightShadow": 3,
        "SpotLight": 3,
        "SpotLightShadow": 3,
    }

    maxPerTileLights = {
        "PointLight": 3,
        "PointLightShadow": 5,
        "DirectionalLight": 3,
        "DirectionalLightShadow": 3,
        "SpotLight": 3,
        "SpotLightShadow": 3,
    }

    maxTotalLights = 6
    maxShadowMaps = 36

