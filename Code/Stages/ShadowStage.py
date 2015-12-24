
from panda3d.core import Camera, NodePath, DepthWriteAttrib
from panda3d.core import DepthTestAttrib

from ..RenderStage import RenderStage
from ..Globals import Globals

class ShadowStage(RenderStage):

    """ This is the stage which renders all shadows """
    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, "ShadowStage", pipeline)
        self._size = 4096

    def set_size(self, size):
        self._size = size

    def get_produced_pipes(self):
        return {
            "ShadowAtlas": self._target["depth"]
        }

    def create(self):
        self._target = self._create_target("ShadowAtlas")
        self._target.set_source(source_cam=NodePath(Camera("dummy_shadow_cam")), source_win=Globals.base.win)
        self._target.set_size(self._size, self._size)
        self._target.add_depth_texture(bits=32)
        self._target.prepare_scene_render()

    def set_shader_input(self, *args):
        Globals.render.set_shader_input(*args)

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
