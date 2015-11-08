
# Load plugin api
from .. import *
from panda3d.core import Vec3

# Load some plugin classes here

# Create the main plugin
class Plugin(BasePlugin):

    NAME = "PSSM"
    DESCRIPTION = """ This plugin adds support for directional shadows using PSSM"""
    SETTINGS = {
        "pssm_distance": PS_Float(min_value=10.0, max_value=3000.0, value=100.0, runtime=True)
    }

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline) 
        self._resolution = 512
        self._sun_distance = 500.0
        self._update_enabled = True

    @PluginHook("on_pipeline_created")
    def init(self):
        self.debug("Init pssm ..")

        # Construct a dummy node to parent the rig to
        self._node = Globals.base.render.attach_new_node("PSSMCameraRig")
        self._node.hide()

        # Construct the actual PSSM rig
        self._rig = PSSMCameraRig(5)
        self._rig.set_sun_distance(self._sun_distance)
        self._rig.reparent_to(self._node)

        # Accept a shortcut to enable / disable the update of PSSM
        Globals.base.accept("u", self._toggle_update_enabled)

    @PluginHook("on_shader_create")
    def create_shaders(self):
        pass

    @PluginHook("pre_render_update")
    def update(self):
        sun_vector = Vec3(0.0, 0.0, 1.0)
        sun_vector.normalize()

        if self._update_enabled:
            self._rig.fit_to_camera(Globals.base.camera, sun_vector)

    @SettingChanged("pssm_distance")
    def update_pssm_distance(self):
        print "Adjusting pssm distance"


    def _toggle_update_enabled(self):
        self._update_enabled = not self._update_enabled
        self.debug("Update enabled:", self._update_enabled)
