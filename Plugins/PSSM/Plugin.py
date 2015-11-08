
# Load plugin api
from .. import *
from panda3d.core import Vec3, NodePath, Camera

# Load some plugin classes here
from PSSMShadowStage import PSSMShadowStage
from PSSMStage import PSSMStage

# Create the main plugin
class Plugin(BasePlugin):

    NAME = "PSSM"
    DESCRIPTION = """ This plugin adds support for directional shadows using PSSM"""
    SETTINGS = {
        "pssm_distance": PS_Float(min_value=10.0, max_value=3000.0, value=40.0, runtime=True),
        "sun_distance": PS_Float(min_value=100.0, max_value=10000.0, value=500.0),
        "split_count": PS_Int(min_value=2, max_value=10, value=5),
        "resolution": PS_Int(min_value=128, max_value=4096, value=2048),
    }

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline) 
        self._resolution = 512
        self._sun_distance = 500.0
        self._update_enabled = True


    @PluginHook("on_stage_setup")
    def setup_stages(self):
        self._shadow_stage = self.make_stage(PSSMShadowStage)
        self._shadow_stage.set_num_splits(self["split_count"])
        self._shadow_stage.set_split_resolution(self["resolution"])
        self.register_stage(self._shadow_stage)

        self._pssm_stage = self.make_stage(PSSMStage)
        self.register_stage(self._pssm_stage)

    @PluginHook("on_pipeline_created")
    def init(self):
        self.debug("Init pssm ..")

        # Construct a dummy node to parent the rig to
        self._node = Globals.base.render.attach_new_node("PSSMCameraRig")
        self._node.hide()

        # Construct the actual PSSM rig
        self._rig = PSSMCameraRig(self["split_count"])
        self._rig.set_sun_distance(self["sun_distance"])
        self._rig.set_pssm_distance(self["pssm_distance"])
        self._rig.reparent_to(self._node)

        # Attach the cameras to the shadow stage
        for i in range(self["split_count"]):
            camera_np = self._rig.get_camera(i)
            camera_np.node().set_scene(Globals.base.render)
            region = self._shadow_stage.get_split_region(i)
            region.set_camera(camera_np)

            # Make sure the pipeline knows about our camera, so it can apply
            # the correct bitmasks
            self._pipeline.get_tag_mgr().register_shadow_source(camera_np)

        # Accept a shortcut to enable / disable the update of PSSM
        Globals.base.accept("u", self._toggle_update_enabled)

        # Set inputs
        self._pssm_stage.set_shader_input("pssm_split_distance", self["pssm_distance"])
        self._pssm_stage.set_shader_input("pssm_split_count", self["split_count"])
        self._pssm_stage.set_shader_input("pssm_mvps", self._rig.get_mvp_array())

    @PluginHook("on_shader_create")
    def create_shaders(self):
        pass

    @PluginHook("pre_render_update")
    def update(self):
        sun_vector = Vec3(0.05, 0.8, 0.4)
        sun_vector.normalize()

        if self._update_enabled:
            self._rig.fit_to_camera(Globals.base.camera, sun_vector)

    @SettingChanged("pssm_distance")
    def update_pssm_distance(self):
        print "Adjusting pssm distance"


    def _toggle_update_enabled(self):
        self._update_enabled = not self._update_enabled
        self.debug("Update enabled:", self._update_enabled)

