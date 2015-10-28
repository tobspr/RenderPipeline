from __future__ import print_function


"""


This tool takes a .egg or .bam file as input, and converts it to
a RPSG file, which can be loaded in the pipeline later on, and 
should be way more performant than rendering a regular model.


Make sure you have setup the pipeline, otherwise this script won't work.

"""


import sys
sys.path.insert(0, "../../")
from Native.RSNative import MeshSplitterWriter
from panda3d.core import Loader, NodePath

# TODO: Make input- and output-file command line parameters, something like:
# convert.py -o output.rpsg input.bam 


INPUT_FILE = "Scene.bam"
OUTPUT_FILE = "model.rpsg"


loader = Loader.get_global_ptr()
model = NodePath(loader.load_sync(INPUT_FILE))

# Flatten the transform of the model, since we don't store the transform
model.flatten_strong()

print("Loaded model ...")
writer = MeshSplitterWriter()

# Collect all geoms of the model and register them to the writer
geom_nodes = model.find_all_matches("**/+GeomNode")
for geom_node in geom_nodes:
    geom_node = geom_node.node()
    for geom_idx in range(geom_node.get_num_geoms()):
        geom = geom_node.get_geom(geom_idx)
        geom_state = geom_node.get_geom_state(geom_idx)
        writer.add_geom(geom)

# Write the result file
print("Processing ....")
writer.process(OUTPUT_FILE)
print("Done!")
