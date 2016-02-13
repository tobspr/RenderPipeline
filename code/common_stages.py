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

from .rp_object import RPObject

from .stages.ambient_stage import AmbientStage
from .stages.gbuffer_stage import GBufferStage
from .stages.final_stage import FinalStage
from .stages.downscale_z_stage import DownscaleZStage

class CommonStages(RPObject):

    """ Setups commonly used stages for the pipeline """

    def __init__(self, pipeline):
        """ Inits the common stages """
        RPObject.__init__(self)
        self._pipeline = pipeline
        self._init_stages()

    def _init_stages(self):
        """ Performs the stage setup """

        add_stage = self._pipeline.stage_mgr.add_stage

        self._ambient_stage = AmbientStage(self._pipeline)
        add_stage(self._ambient_stage)

        self._gbuffer_stage = GBufferStage(self._pipeline)
        add_stage(self._gbuffer_stage)

        self._final_stage = FinalStage(self._pipeline)
        add_stage(self._final_stage)

        # self._downscale_z_stage = DownscaleZStage(self._pipeline)
        # self._pipeline.stage_mgr.add_stage(self._downscale_z_stage)
