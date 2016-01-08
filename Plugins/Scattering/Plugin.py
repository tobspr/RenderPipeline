"""

RenderPipeline

Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>

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

from .. import *

from .ScatteringStage import ScatteringStage

# Create the main plugin
class Plugin(BasePlugin):

    @PluginHook("on_pipeline_created")
    def on_create(self):
        self._method.load()
        self._method.compute()

    @PluginHook("on_stage_setup")
    def on_setup(self):
        self.debug("Setting up scattering stage ..")
        self._display_stage = self.create_stage(ScatteringStage)

        # Load scattering method
        method = self.get_setting("scattering_method")

        self.debug("Loading scattering method for '" + method + "'")

        if method == "eric_bruneton":
            from .ScatteringMethods import ScatteringMethodEricBruneton
            self._method = ScatteringMethodEricBruneton(self)
        elif method == "hosek_wilkie":
            from .ScatteringMethods import ScatteringMethodHosekWilkie
            self._method = ScatteringMethodHosekWilkie(self)
        else:
            self.error("Unrecognized scattering method!")

    @PluginHook("on_shader_reload")
    def on_shader_reload(self):
        self._method.compute()
