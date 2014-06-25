
from panda3d.core import loadPrcFileData
from MeshSimplifier import MeshSimplifier


loadPrcFileData("", """
win-size 1600 900
""".strip())

import direct.directbase.DirectStart

scene = loader.loadModel("Scene/Scene")
base.camera.setPos(5, 0.5, 0)
base.camera.lookAt(scene)

base.accept("f3", base.toggleWireframe)

base.toggleWireframe()

simplified = MeshSimplifier.simplifyNodePath(scene, 140)
simplified.reparentTo(render)
simplified.setPos(1,0,0)

run()
