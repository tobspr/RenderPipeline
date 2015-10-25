



from panda3d.core import *
from random import random
import direct.directbase.DirectStart

import sys
sys.path.insert(0, "../../")

from Native.RSNative import StaticGeometryHandler, SGNode, SGFinishNode

# This is usually done by the pipeline
handler = StaticGeometryHandler()
finish_node = SGFinishNode(handler)
finish_np = render.attach_new_node(finish_node)

# Load model
model_dataset = handler.load_dataset("model.rpsg")
node = SGNode("test", handler, model_dataset)
np = render.attach_new_node(node)
# np.set_pos(10, 10, 5)
# np.set_scale(0.5)


base.run()

sys.exit(0)












################## OLD CODE ####################


with open("model.rpsg", "rb") as handle:
    data = handle.read()


dg = Datagram(data)
dgi = DatagramIterator(dg)

header = dgi.get_fixed_string(4)
num_strips = dgi.get_uint32()

if header != "RPSG":
    print "Missing RPSG header (was: "  + header + ")!"
    sys.exit(0)

v = 0

def get_color():
    return Vec4(random(), random(), random(), 1)


root_gn = GeomNode("geomNode")


def generate_geom(tri_list):
    
    vformat = GeomVertexFormat.get_v3()
    vdata = GeomVertexData("vdata", vformat, Geom.UH_static)
    vdata.set_num_rows(len(tri_list))

    vwriter = GeomVertexWriter(vdata, "vertex")

    for tri in tri_list:
        for vtx in tri:
            vwriter.add_data3f(vtx + Vec3(0, 0, v * 0.0))

    triangles = GeomTriangles(Geom.UH_static)

    triangles.add_next_vertices( len(tri_list) * 3)
    # triangles.add_consecutive_vertices(0, len(tri_list) * 3)

    
    gstate = RenderState.make(ColorAttrib.make_flat(get_color()))

    geom = Geom(vdata)
    geom.add_primitive(triangles)
    root_gn.add_geom(geom, gstate)


for idx in range(num_strips):
    if idx % 500 == 0:
        print "Processing strip", idx


    num_tris = dgi.get_uint32()

    triangles = []

    for tidx in range(num_tris):

        vertices = []

        for i in range(3):
            vx = dgi.get_float32()
            vy = dgi.get_float32()
            vz = dgi.get_float32()
            
            nx = dgi.get_float32()
            ny = dgi.get_float32()
            nz = dgi.get_float32()

            u = dgi.get_float32()
            v = dgi.get_float32()

            vertices.append(Vec3(vx, vy, vz))

        triangles.append(vertices)


    generate_geom(triangles)



np = render.attach_new_node(root_gn)
np.set_two_sided(True)
base.accept("f3", base.toggleWireframe)

run()