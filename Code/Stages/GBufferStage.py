
from panda3d.core import Camera, NodePath, DepthWriteAttrib
from panda3d.core import DepthTestAttrib

from ..RenderStage import RenderStage
from ..Globals import Globals
from ..Util.ShaderUBO import SimpleUBO

class GBufferStage(RenderStage):

    """ This is the main pass stage, rendering the objects and creating the
    GBuffer which is used in later stages """

    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, "GBufferStage", pipeline)

    def get_produced_pipes(self):
        return {
            "GBuffer": self._make_gbuffer_ubo()
        }

    def _make_gbuffer_ubo(self):
        ubo = SimpleUBO("GBuffer")
        ubo.add_input("Depth", self._target["depth"])
        ubo.add_input("Data0", self._target["color"])
        ubo.add_input("Data1", self._target["aux0"])
        ubo.add_input("Data2", self._target["aux1"])
        return ubo

    def create(self):
        early_z = False
        self._prepare_early_z(early_z)
        self._target = self._create_target("GBuffer")
        self._target.add_color_and_depth(color_bits=16, depth_bits=32)
        self._target.add_aux_textures(2, bits=16)

        if early_z:
            self._target.prepare_scene_render(early_z=True,
                                              early_z_cam=self._prepass_cam_node)
        else:
            self._target.prepare_scene_render()

    def _prepare_early_z(self, early_z=False):
        """ Prepares the earlyz stage """
        if early_z:
            self._prepass_cam = Camera(Globals.base.camNode)
            self._prepass_cam.set_tag_state_key("EarlyZShader")
            self._prepass_cam.set_name("EarlyZCamera")
            self._prepass_cam_node = Globals.base.camera.attach_new_node(
                self._prepass_cam)
            Globals.render.set_tag("EarlyZShader", "Default")
        else:
            self._prepass_cam = None

        # modify default camera initial state
        initial = Globals.base.camNode.get_initial_state()
        initial_node = NodePath("IntialState")
        initial_node.set_state(initial)

        if early_z:
            initial_node.set_attrib(
                DepthWriteAttrib.make(DepthWriteAttrib.M_off))
            initial_node.set_attrib(
                DepthTestAttrib.make(DepthTestAttrib.M_equal))
        else:
            initial_node.set_attrib(
                DepthTestAttrib.make(DepthTestAttrib.M_less_equal))

        Globals.base.camNode.set_initial_state(initial_node.get_state())

    def set_shader_input(self, *args):
        Globals.render.set_shader_input(*args)

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
