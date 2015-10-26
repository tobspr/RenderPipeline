from __future__ import print_function

import sys
sys.path.insert(0, "../../")

from Native.RSNative import MeshSplitterWriter

import direct.directbase.DirectStart
from panda3d.core import *


dest = "model.rpsg"

# model = loader.loadModel("Scene.bam")
# model = loader.loadModel("panda")
model = loader.loadModel("test_model.bam")

model.flatten_strong()


writer = MeshSplitterWriter()

geom_nodes = model.find_all_matches("**/+GeomNode")
for geom_node in geom_nodes:
    geom_node = geom_node.node()
    for geom_idx in range(geom_node.get_num_geoms()):
        geom = geom_node.get_geom(geom_idx)
        geom_state = geom_node.get_geom_state(geom_idx)
        # MeshSplitter.split_geom(geom, "model.rpsg", True)
        # sys.exit(0)
        writer.add_geom(geom)


writer.process("model.rpsg")
