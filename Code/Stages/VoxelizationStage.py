
from ..RenderStage import RenderStage

class VoxelizationStage(RenderStage):

    """ This stage voxelizes the whole scene """

    required_inputs = []
    required_pipes = [s]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "VoxelizationStage", pipeline)

    def get_produced_pipes(self):
        return {"ShadedScene": self._target['color']}

    def create(self):
        pass

    def set_shaders(self):
        pass
