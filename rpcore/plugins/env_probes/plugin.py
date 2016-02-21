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

from panda3d.core import Vec3

from rpcore.globals import Globals
from rpcore.pluginbase.base_plugin import BasePlugin

from .probes import EnvironmentProbe, ProbeManager
from .capture_stage import EnvironmentCaptureStage
from .apply_cubemaps_stage import ApplyCubemapsStage

class Plugin(BasePlugin):

    name = "Environment Probes"
    author = "tobspr <tobias.springer1@gmail.com>"
    description = ("This plugin adds support for environment probes, containing "
                   "diffuse and specular information. This enables accurate "
                   "reflections, and can also be used to simulate GI.")
    version = "alpha (!)"


    def on_stage_setup(self):
        self.probe_mgr = ProbeManager(512)
        self.probe_mgr.add_probe(EnvironmentProbe(Vec3(0, 1, 2.0), 20))

        # visualizer = Globals.loader.loadModel("data/builtin_models/visualizer/cubemap.bam")
        # visualizer.reparent_to(render)
        # visualizer.set_pos(0, 1, 2.0)

        self.capture_stage = self.create_stage(EnvironmentCaptureStage)
        self.capture_stage.resolution = self.probe_mgr.resolution
        self.capture_stage.storage_tex = self.probe_mgr.storage_tex

        self.apply_stage = self.create_stage(ApplyCubemapsStage)

        if self.is_plugin_enabled("scattering"):
            self.capture_stage.required_pipes += [
            "ScatteringIBLSpecular", "ScatteringIBLDiffuse"]

        if self.is_plugin_enabled("pssm"):
            self.capture_stage.required_pipes.append("PSSMSceneSunShadowMapPCF")
            self.capture_stage.required_inputs.append("PSSMSceneSunShadowMVP")

    def on_pipeline_created(self):
        self.apply_stage.set_shader_input("CubemapStorage", self.probe_mgr.storage_tex)

    def on_pre_render_update(self):
        probe = self.probe_mgr.find_probe_to_update()
        self.capture_stage.render_probe(probe)

