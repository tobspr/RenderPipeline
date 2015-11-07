
# Load plugin api
from .. import *
from panda3d.core import Vec3

# Load some plugin classes here

# Create the main plugin
class Plugin(BasePlugin):

    NAME = "PSSM"
    DESCRIPTION = """ This plugin adds support for directional shadows using PSSM"""
    SETTINGS = {}

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline) 

    @PluginHook("on_pipeline_created")
    def init(self):
        self.debug("Init pssm ..")
        self._rig = PSSMCameraRig(5)
        self._update_enabled = True
        self._node = Globals.base.render.attach_new_node("PSSMCameraRig")
        self._rig.reparent_to(self._node)
        Globals.base.accept("u", self._toggle_update_enabled)

    @PluginHook("on_shader_create")
    def create_shaders(self):
        pass

    @PluginHook("pre_render_update")
    def update(self):
        sun_vector = Vec3(0.2, 0.3, 1.0)
        sun_vector.normalize()

        if self._update_enabled:
            self._rig.fit_to_camera(Globals.base.camera, sun_vector)

    def _toggle_update_enabled(self):
        self._update_enabled = not self._update_enabled
        self.debug("Update enabled:", self._update_enabled)
