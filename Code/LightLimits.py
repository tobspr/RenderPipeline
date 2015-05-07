

class LightLimits:

    """ This class stores the hardcoded maximum numbers of lights and shadowmaps """

    maxLights = {
        "PointLight": 0,
        "PointLightShadow": 7,
        "DirectionalLight": 1,
        "DirectionalLightShadow": 1,
        "SpotLight": 3,
        "SpotLightShadow": 1,
        "GIHelperLightShadow": 10
    }

    maxPerTileLights = {
        "PointLight": 0,
        "PointLightShadow": 7,
        "DirectionalLight": 1,
        "DirectionalLightShadow": 1,
        "SpotLight": 3,
        "SpotLightShadow": 1,
    }

    maxTotalLights = 8
    maxShadowMaps = 46

