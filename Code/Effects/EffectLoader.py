
from Effect import Effect


class EffectLoader:

    def __init__(self):
        self._effect_cache = {}

    def load_effect(self, filename, options):
        """ Loads an effect from a given filename with the specified options """
        effect_hash = Effect._generate_hash(filename, options)

        # Check if the effect already exists in the cache
        if effect_hash in self._effect_cache:
            return self._effect_cache[effect_hash]

        effect = Effect()
        effect.set_options(options)

        if not effect.load(filename):
            print "Could not load effect!"
            return False

        return effect
