

class LightLimits:

    """ This class stores the hardcoded maximum numbers of lights and shadowmaps.
    The maximum numbers depend on the maximum available uniform shader inputs,
    and may vary, but for now we hardcode this values. """

    maxLights = {
        "PointLight": 15,
        "PointLightShadow": 5,
        "DirectionalLight": 1,
        "DirectionalLightShadow": 1,
        "SpotLight": 3,
        "SpotLightShadow": 1,
        "GIHelperLightShadow": 10
    }

    maxPerTileLights = {
        "PointLight": 15,
        "PointLightShadow": 5,
        "DirectionalLight": 1,
        "DirectionalLightShadow": 1,
        "SpotLight": 3,
        "SpotLightShadow": 1,
    }

    maxTotalLights = 10
    maxShadowMaps = 36

