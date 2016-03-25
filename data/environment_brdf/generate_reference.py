"""

Uses mitsuba to generate the environment brdf

"""

from __future__ import print_function

import os
import sys
import math
from panda3d.core import PNMImage, load_prc_file_data, Vec3

load_prc_file_data("", "notify-level error")
load_prc_file_data("", "notify-level-pnmimage error")

if not os.path.isdir("slices"):
    os.makedirs("slices")

for ior_index in xrange(15):
    ior = 1.01 + 0.1 * ior_index

    dest_size = 512
    dest_h = 32
    dest = PNMImage(dest_size, dest_h)

    # run mitsuba
    print("Running mitsuba for ior =", ior, "( index =", ior_index,")")
    with open("res/scene.templ.xml", "r") as handle:
        content = handle.read()

    content = content.replace("%IOR%", str(ior))

    with open("res/scene.xml", "w") as handle:
        handle.write(content)

    os.system("run_mitsuba.bat")

    img = PNMImage("scene.png")
    source_w = img.get_x_size()

    print("Converting ..")

    indices = []
    nxv_values = []

    for i in xrange(source_w):
        v = 1 - i / float(source_w)
        NxV = math.sqrt(1 - v*v)
        nxv_values.append(NxV)

    for x in xrange(dest_size):
        NxV = (x) / float(dest_size)
        # print("Searaching", NxV)
        index = 0
        for i, s_nxv in enumerate(reversed(nxv_values)):
            if NxV >= s_nxv:
                index = i
                break
        index = len(nxv_values) - index - 1
        # print("Found sample at", index)

        next_index = index + 1 if index < dest_size - 1 else index

        curr_nxv = nxv_values[index]
        next_nxv = nxv_values[next_index]

        lerp_factor = (NxV - curr_nxv) / max(1e-10, abs(next_nxv - curr_nxv))
        lerp_factor = max(0.0, min(1.0, lerp_factor))
        # print("Lerp=", lerp_factor, "curr=", curr_nxv, "next=", next_nxv, "nxv=", NxV, "index=", index, "next=", next_index)

        indices.append((index, next_index, lerp_factor))

    for y in xrange(dest_h):
        for x in xrange(dest_size):
            curr_i, next_i, lerp = indices[x]

            curr_v = img.get_xel(curr_i, y)
            next_v = img.get_xel(next_i, y)

            dest.set_xel(x, y, curr_v * (1 - lerp) + next_v * lerp)


    dest.write("slices/env_brdf_" + str(ior_index) + ".png")

try:
    os.remove("scene.png")
except:
    pass
