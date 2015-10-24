


from panda3d.core import *
from random import random
import direct.directbase.DirectStart


with open("model.rpsg", "r") as handle:
    lines = handle.readlines()

v = 0

def get_c():
    return Vec4(random(), random(), random(), 1)
    global v
    v += 1
    return Vec4(v / 1000.0,  1.0 - (v / 1000.0), v % 2, 1)

def read_vec(s):
    data = [float(i) for i in s.split(",")[0:3]]
    return Vec3(*data)

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

    
    gstate = RenderState.make(ColorAttrib.make_flat(get_c()))

    geom = Geom(vdata)
    geom.add_primitive(triangles)
    root_gn.add_geom(geom, gstate)


for idx, line in enumerate(lines):
    if idx % 500 == 0:
        print "Processing strip", idx
    line = line.strip()
    if len(line) < 1:
        continue

    tris = line.split("|")
    vstrip = []
    for tri in tris:
        if len(tri) < 1:
            continue
        vtxs = [read_vec(s) for s in tri.split("/")[0:3]]
        vstrip.append(vtxs)

    generate_geom(vstrip)



np = render.attach_new_node(root_gn)
np.set_two_sided(True)
base.accept("f3", base.toggleWireframe)

run()