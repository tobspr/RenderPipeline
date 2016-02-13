"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
 	 	    	 	
"""

from .Effect import Effect
from ..Util.DebugObject import DebugObject


class EffectLoader(DebugObject):

    """ This class handles the loading and caching of effects """

    def __init__(self):
        DebugObject.__init__(self)
        self._effect_cache = {}

    def load_effect(self, filename, options):
        """ Loads an effect from a given filename with the specified options """
        effect_hash = Effect.generate_hash(filename, options)
        # Check if the effect already exists in the cache
        if effect_hash in self._effect_cache:
            return self._effect_cache[effect_hash]

        effect = Effect()
        effect.set_options(options)

        if not effect.load(filename):
            self.error("Could not load effect!")
            return None

        return effect
