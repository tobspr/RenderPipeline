from __future__ import division

from panda3d.core import ComputeNode, Shader, Vec4, Texture, Vec3
from direct.gui.DirectFrame import DirectFrame

from ..Util.DebugObject import DebugObject
from ..Util.Image import Image
from ..Globals import Globals

from .BetterOnscreenImage import BetterOnscreenImage
from .BetterOnscreenText import BetterOnscreenText

class ExposureWidget(DebugObject):

    """ Widget to show the current exposure """

    def __init__(self, pipeline, parent):
        """ Inits the widget """
        DebugObject.__init__(self)
        self._pipeline = pipeline
        self._parent = parent
        self._node = self._parent.attach_new_node("ExposureWidgetNode")
        self._create_components()


    def _create_components(self):
        """ Internal method to init the widgets components """
        
        self._node.hide()

        # Create the texture where the gui component is rendered inside
        self._storage_tex = Image.create_2d("ExposureDisplay", 140, 20, Texture.T_unsigned_byte, Texture.F_rgba8)
        self._storage_tex.set_clear_color(Vec4(0.2, 0.6, 1.0, 1.0))
        self._storage_tex.clear_image()

        self._bg_frame = DirectFrame(parent=self._node, frameColor=(0.1, 0.1, 0.1, 1.0),
                                     frameSize=(200, 0, -10, -85), pos=(0, 0, 0))

        self._display_img = BetterOnscreenImage(
            image=self._storage_tex.get_texture(), parent=self._node, w=140, h=20, x=20, y=50)

        self._display_txt = BetterOnscreenText(
            text="Current Exposure".upper(), parent=self._node, x=160, y=40, size=13,
            color=Vec3(0.8), align="right")

        # Create the shader which generates the visualization texture
        self._cshader_node = ComputeNode("ExposureWidget")
        self._cshader_node.add_dispatch(140 // 10, 20 // 4, 1)

        self._cshader_np = self._node.attach_new_node(self._cshader_node)

        # Defer the further loading
        Globals.base.taskMgr.doMethodLater(1.0, self._late_init, "ExposureLateInit")

    def _late_init(self, task):
        """ Gets called after the pipeline initialized, this extracts the
        exposure texture from the stage manager """

        stage_mgr = self._pipeline.get_stage_mgr()

        if not stage_mgr.has_pipe("Exposure"):
            self.warn("Disabling exposure widget, could not find the exposure texture.")
            self._node.remove_node()
            return

        self._node.show()

        exposure_tex = stage_mgr.get_pipe("Exposure")

        self._cshader = Shader.load_compute(Shader.SL_GLSL, "Shader/GUI/VisualizeExposure.compute.glsl")
        self._cshader_np.set_shader(self._cshader)
        self._cshader_np.set_shader_input("DestTex", self._storage_tex.get_texture())
        self._cshader_np.set_shader_input("ExposureTex", exposure_tex)
