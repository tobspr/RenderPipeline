"""

RP Distributor

"""

from __future__ import print_function


import re
import os
import sys
import shutil
from os.path import isfile, isdir, join, dirname, realpath, relpath

base_dir = realpath(dirname(__file__))
rp_dir = realpath(join(base_dir, "../../"))
os.chdir(base_dir)

sys.path.insert(0, rp_dir)
from rplibs.six.moves import input

ignores = [

    # data
    "skybox-blend.zip",
    "skybox.jpg",
    "skybox-2.jpg",
    "default_cubemap/source",
    "default_cubemap/source_2",
    "default_cubemap/filter.compute.glsl",
    "default_cubemap/filter.py",
    "data/generate_txo_files.py",
    "README.md",
    "environment_brdf/generate_reference.py",
    "run_mitsuba.bat",
    ".mip",
    ".xml",
    ".exr",
    ".psd",
    ".diff",
    ".pyc",
    ".pdb",
    "environment_brdf/res/",
    "film_grain/generate.py",
    "film_grain/grain.compute.glsl",
    "ies_profiles/PREVIEWS.jpg",

    # rpcore
    "native/scripts",
    "native/source",
    "native/win_amd",
    "native/win_i386",
    "native/.gitignore",
    "native/build.py",
    "native/CMakeLists",
    "native/update_module_builder.py",
    "native/config.ini",

    # rpplugins
    ".ffxml",
    "bloom/resources/SOURCE.txt",
    "bloom/resources/lens_dirt.png",
    "clouds/resources/generate_",
    "clouds/resources/noise.inc",
    "clouds/resources/precompute.py",
    "color_correction/resources/film_luts_raw",
    "color_correction/resources/generate_",
    "plugin_prefab",
    "scattering/resources/hosek_wilkie_scattering",

    # Avoid infinite recursion
    "rp_distributor",
    
    # toolkit
    "ui/res",
    "compile_ui.bat",
    ".ui",
    ".qrc",
    "pathtracing_reference",
    "poisson_disk_generator",
    "render_service/resources",



]


def distribute():
    print("Render Pipeline Distributor v0.1")
    print("")
    print("Copying tree ..")

    tmp_dir = join(base_dir, "render_pipeline_v2")
    dest_dir = join(tmp_dir, "render_pipeline")
    if isdir(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(dest_dir)

    def copy_tree(tree_pth):
        source = join(rp_dir, tree_pth)
        dest = join(dest_dir, tree_pth)
        for basepath, dirnames, files in os.walk(source):
            for f in files:
                abspath = realpath(join(basepath, f))
                abspath = abspath.replace("\\", "/")

                for ignore in ignores:
                    if ignore in abspath:
                        break
                else:
                    local_pth = relpath(abspath, start=source)
                    dest_pth = join(dest, local_pth)
                    dname = dirname(dest_pth)
                    if not isdir(dname):
                        print("Creating", dname)
                        os.makedirs(dname)
                    shutil.copyfile(abspath, dest_pth)

    copy_tree("config")
    copy_tree("data")
    copy_tree("rplibs")
    copy_tree("effects")
    copy_tree("rpcore")
    copy_tree("rpplugins")
    copy_tree("toolkit")

    shutil.copyfile(join(rp_dir, "__init__.py"), join(dest_dir, "__init__.py"))
    shutil.copyfile(join(rp_dir, "README.md"), join(tmp_dir, "README.md"))
    shutil.copyfile(join(rp_dir, "LICENSE.txt"), join(tmp_dir, "LICENSE.txt"))
    shutil.copyfile(join(base_dir, "whl-setup.tmpl.py"), join(tmp_dir, "setup.py"))
    shutil.copyfile(join(base_dir, "whl-setup.tmpl.cfg"), join(tmp_dir, "setup.cfg"))

if __name__ == "__main__":
    distribute()
