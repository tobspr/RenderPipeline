
from panda3d.core import Shader, Camera, NodePath, DepthWriteAttrib
from panda3d.core import DepthTestAttrib

from ..RenderStage import RenderStage
from ..Globals import Globals


class GBufferStage(RenderStage):

    """ This is the main pass stage, rendering the objects and creating the
    GBuffer which is used in later stages """

    def __init__(self, pipeline):
        RenderStage.__init__(self, "GBufferStage", pipeline)

    def get_produced_pipes(self):
        return {
            "GBufferDepth": self._target.getDepthTexture(),
            "GBuffer0": self._target.getColorTexture(),
            "GBuffer1": self._target.getAuxTexture(0),
            "GBuffer2": self._target.getAuxTexture(1),
        }

    def create(self):
        early_z = True

        self._prepare_early_z(early_z)

        self._target = self._create_target("GBuffer")
        self._target.addDepthTexture()
        self._target.addColorTexture()
        self._target.addAuxTextures(2)
        self._target.setDepthBits(32)
        # self._target.setColorBits(16)

        if early_z:
            self._target.prepareSceneRender(earlyZ=True,
                                            earlyZCam=self._prepass_cam_node)
        else:
            self._target.prepareSceneRender()

    def _prepare_early_z(self, early_z=False):
        """ Prepares the earlyz stage """
        if early_z:
            self._prepass_cam = Camera(Globals.base.camNode)
            self._prepass_cam.set_tag_state_key("EarlyZShader")
            self._prepass_cam.set_name("EarlyZCamera")
            self._prepass_cam_node = Globals.base.camera.attach_new_node(
                self._prepass_cam)
            Globals.render.setTag("EarlyZShader", "Default")
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

    def set_shaders(self):
        Globals.render.setShader(Shader.load(Shader.SL_GLSL,
            "Shader/Templates/Vertex.glsl",
            "Shader/Templates/Stages/GBuffer-Fragment.glsl"))

    def set_shader_input(self, *args):
        Globals.render.setShaderInput(*args)

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
