

import hashlib
import sys
sys.path.insert(0, "../")

from Effect import Effect


class EffectLoader():

    def __init__(self):
        self.effectCache = {}

    def loadEffect(self, filename, options):
        """ Loads an effect from a given filename with the specified options """
        effectHash = Effect._generateHash(filename, options)

        # Check if the effect already exists in the cache
        if effectHash in self.effectCache:
            return self.effectCache[effectHash]

        effect = Effect()
        effect.setOptions(options)

        if not effect.load(filename):
            print "Could not load effect!"
            return False

        return effect

if __name__ == "__main__":
    
    l = EffectLoader()
    l.loadEffect("../../Effects/Default.yaml", {})