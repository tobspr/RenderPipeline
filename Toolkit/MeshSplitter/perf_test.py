

from panda3d.core import *
load_prc_file_data("", "show-frame-rate-meter #t")

import direct.directbase.DirectStart

import sys
sys.path.insert(0, "../../")


from Code.Util.MovementController import MovementController


controller = MovementController(base)
controller.set_initial_position(Vec3(5), Vec3(0))
controller.setup()


model = loader.loadModel("Scene.bam")
model.reparent_to(render)


base.run()
