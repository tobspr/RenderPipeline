

class LightLimits:

    """ This class stores the hardcoded maximum numbers of lights and shadowmaps.
    The maximum numbers depend on the maximum available uniform shader inputs,
    and may vary, but for now we hardcode this values. """

    maxLights = {
        "PointLight": 30,
        "PointLightShadow": 30,
        "DirectionalLight": 30,
        "DirectionalLightShadow": 30,
        "SpotLight": 30,
        "SpotLightShadow": 30,
        "GIHelperLightShadow": 30
    }

    maxPerTileLights = {
        "PointLight": 30,
        "PointLightShadow": 30,
        "DirectionalLight": 30,
        "DirectionalLightShadow": 30,
        "SpotLight": 30,
        "SpotLightShadow": 30,
    }

    maxTotalLights = 19
    maxShadowMaps = 19

