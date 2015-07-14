
from Effect import Effect

from DebugObject import DebugObject

class EffectLoader(DebugObject):

    def __init__(self, pipeline):
        DebugObject.__init__(self, "EffectLoader")
        self.effectCache = {}
        self.pipeline = pipeline

    def loadEffect(self, filename, effectSettings=None):
        """ Loads an effect from a given file with the given effect settings """


        effect = Effect()

        cache_name = filename + "#" + effect.getSerializedSettings(effectSettings)
        if cache_name in self.effectCache:
            del effect
            return self.effectCache[cache_name]

        if effectSettings is not None:
            effect.setSettings(effectSettings)

        effect.load(filename)
        self.effectCache[cache_name] = effect

        return effect
