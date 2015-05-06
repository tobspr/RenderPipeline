

class LightLimits:

    """ This class stores the hardcoded maximum numbers of lights and shadowmaps """

    maxLights = {
        "PointLight": 15,
        "PointLightShadow": 4,
        "DirectionalLight": 1,
        "DirectionalLightShadow": 1,
        "SpotLight": 3,
        "SpotLightShadow": 1,
        "GIHelperLightShadow": 10
    }

    maxPerTileLights = {
        "PointLight": 15,
        "PointLightShadow": 4,
        "DirectionalLight": 1,
        "DirectionalLightShadow": 1,
        "SpotLight": 3,
        "SpotLightShadow": 1,
    }

    maxTotalLights = 20
    maxShadowMaps = 24

