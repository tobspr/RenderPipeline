
from Effect import Effect

class EffectLoader:

    def __init__(self):
        self.effectCache = {}

    def load_effect(self, filename, options):
        """ Loads an effect from a given filename with the specified options """
        effect_hash = Effect._generate_hash(filename, options)

        # Check if the effect already exists in the cache
        if effect_hash in self.effectCache:
            return self.effectCache[effect_hash]

        effect = Effect()
        effect.set_options(options)

        if not effect.load(filename):
            print "Could not load effect!"
            return False

        return effect
