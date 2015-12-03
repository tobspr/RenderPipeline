
from __future__ import print_function

from math import cos, sin, pi

from panda3d.core import Vec3, PTAVecBase3f

from .. import *
from .PSSMShadowStage import PSSMShadowStage
from .PSSMStage import PSSMStage

class Plugin(BasePlugin):

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        self._update_enabled = True
        self._pta_sun_vector = PTAVecBase3f.empty_array(1)
        self._last_cache_reset = 0

        self._shadow_stage = self.create_stage(PSSMShadowStage)
        self._pssm_stage = self.create_stage(PSSMStage)

        self._shadow_stage.set_num_splits(self.get_setting("split_count"))
        self._shadow_stage.set_split_resolution(self.get_setting("resolution"))

    @PluginHook("on_pipeline_created")
    def init(self):
        self.debug("Init pssm ..")

        # Construct a dummy node to parent the rig to
        self._node = Globals.base.render.attach_new_node("PSSMCameraRig")
        self._node.hide()

        # Construct the actual PSSM rig
        self._rig = PSSMCameraRig(self.get_setting("split_count")) # pylint: disable=E0602
        self._rig.set_sun_distance(self.get_setting("sun_distance"))
        self._rig.set_pssm_distance(self.get_setting("max_distance"))
        self._rig.set_logarithmic_factor(self.get_setting("logarithmic_factor"))
        self._rig.set_use_stable_csm(True)
        self._rig.set_use_fixed_film_size(False)
        self._rig.set_use_tight_frustum(True)
        self._rig.set_resolution(self.get_setting("resolution"))

        self._rig.reparent_to(self._node)

        # Attach the cameras to the shadow stage
        for i in range(self.get_setting("split_count")):
            camera_np = self._rig.get_camera(i)
            camera_np.node().set_scene(Globals.base.render)
            region = self._shadow_stage.get_split_region(i)
            region.set_camera(camera_np)

            # camera_np.node().show_frustum()

            # Make sure the pipeline knows about our camera, so it can apply
            # the correct bitmasks
            self._pipeline.get_tag_mgr().register_shadow_source(camera_np)

        # Accept a shortcut to enable / disable the update of PSSM
        Globals.base.accept("u", self._toggle_update_enabled)

        # Set inputs
        self._pssm_stage.set_shader_input("pssm_split_count", self.get_setting("split_count"))
        self._pssm_stage.set_shader_input("pssm_mvps", self._rig.get_mvp_array())
        self._pssm_stage.set_shader_input("pssm_rotations", self._rig.get_rotation_array())
        self._pssm_stage.set_shader_input("pssm_sun_vector", self._pta_sun_vector)

    @PluginHook("pre_render_update")
    def update(self):

        if not self.is_plugin_loaded("Scattering"):
            sun_vector = Vec3(0.3, 0.3, 0.5)
            sun_vector.normalize()
        else:
            sun_altitude = self.get_daytime_setting(
                "sun_altitude", plugin_id="Scattering")
            sun_azimuth = self.get_daytime_setting(
                "sun_azimuth", plugin_id="Scattering")

            theta = (90 - sun_altitude) / 180.0 * pi
            phi = sun_azimuth / 180.0 * pi

            sun_vector = Vec3(
                sin(theta) * cos(phi),
                sin(theta) * sin(phi),
                cos(theta))

        self._pta_sun_vector[0] = sun_vector

        if self._update_enabled:
            self._rig.fit_to_camera(Globals.base.camera, sun_vector)

            # Eventually reset cache
            cache_diff = Globals.clock.get_frame_time() - self._last_cache_reset
            if cache_diff > 1.0:
                self._last_cache_reset = Globals.clock.get_frame_time()
                self._rig.reset_film_size_cache()

    @SettingChanged("max_distance")
    def update_pssm_distance(self):
        self._rig.set_pssm_distance(self.get_setting("max_distance"))

    @SettingChanged("logarithmic_factor")
    def update_log_factor(self):
        self._rig.set_logarithmic_factor(self.get_setting("logarithmic_factor"))

    @SettingChanged("sun_distance")
    def update_sun_distance(self):
        self._rig.set_sun_distance(self.get_setting("sun_distance"))

    def _toggle_update_enabled(self):
        self._update_enabled = not self._update_enabled
        self.debug("Update enabled:", self._update_enabled)

