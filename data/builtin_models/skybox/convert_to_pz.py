"""

Converts the skydome to a txo file.

"""

import os
from panda3d.core import *
load_prc_file_data("", "window-type none")

import direct.directbase.DirectStart


# Convert skytex
tex = loader.load_texture("skybox-1.jpg")
tex.write("skybox.txo.pz")

# Convert skybox model
model = loader.load_model("skybox.bam")
model.write_bam_file("skybox.bam.pz")
