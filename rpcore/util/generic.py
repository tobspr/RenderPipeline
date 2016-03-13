"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

import hashlib
import time
from rplibs.six.moves import range

from panda3d.core import PNMImage, VirtualFileSystem, VirtualFileMountRamdisk
from panda3d.core import PStatCollector

from rpcore.globals import Globals

def rgb_from_string(text, min_brightness=0.6):
    """ Creates a rgb color from a given string """
    ohash = hashlib.md5(text[::-1].encode("ascii")).hexdigest()
    r, g, b = int(ohash[0:2], 16), int(ohash[2:4], 16), int(ohash[4:6], 16)
    neg_inf = 1.0 - min_brightness
    return (min_brightness + r / 255.0 * neg_inf,
            min_brightness + g / 255.0 * neg_inf,
            min_brightness + b / 255.0 * neg_inf)


def load_sliced_3d_texture(fname, tile_size_x, tile_size_y=None, num_tiles=None):
    """ Loads a texture from the given filename and dimensions. If only
    one dimensions is specified, the other dimensions are assumed to be
    equal. This internally loads the texture into ram, splits it into smaller
    sub-images, and then calls the load_3d_texture from the Panda loader """

    # Generate a unique name to prevent caching
    tempfile_name = "/$$slide_loader_temp-" + str(time.time()) + "/"

    # For quaddratic textures
    tile_size_y = tile_size_x if tile_size_y is None else tile_size_y
    num_tiles = tile_size_x if num_tiles is None else num_tiles

    # Load sliced image from disk
    source = PNMImage(fname)
    width = source.get_x_size()

    # Find slice properties
    num_cols = width // tile_size_x
    temp = PNMImage(
        tile_size_x, tile_size_y, source.get_num_channels(), source.get_maxval())

    # Construct a ramdisk to write the files to
    vfs = VirtualFileSystem.get_global_ptr()
    ramdisk = VirtualFileMountRamdisk()
    vfs.mount(ramdisk, tempfile_name, 0)

    # Extract all slices and write them to the virtual disk
    for z_slice in range(num_tiles):
        slice_x = (z_slice % num_cols) * tile_size_x
        slice_y = (z_slice // num_cols) * tile_size_y
        temp.copy_sub_image(source, 0, 0, slice_x, slice_y, tile_size_x, tile_size_y)
        temp.write(tempfile_name + str(z_slice) + ".png")

    # Load the de-sliced texture from the ramdisk
    texture_handle = Globals.loader.load_3d_texture(tempfile_name + "/#.png")

    # This should never trigger, but can't hurt to have
    assert texture_handle.get_x_size() == tile_size_x
    assert texture_handle.get_y_size() == tile_size_y
    assert texture_handle.get_z_size() == num_tiles

    # Finally unmount the ramdisk
    vfs.unmount(ramdisk)

    return texture_handle

def profile(func):
    """ Handy decorator which can be used to profile a function with pstats """
    collector_name = "Debug:%s" % func.__name__

    global_showbase = Globals.base

    # Insert the collector to a custom dictionary attached to the base
    if hasattr(global_showbase, 'custom_collectors'):
        if collector_name in global_showbase.custom_collectors.keys():
            pstat = global_showbase.custom_collectors[collector_name]
        else:
            global_showbase.custom_collectors[collector_name] = \
                PStatCollector(collector_name)
            pstat = global_showbase.custom_collectors[collector_name]
    else:
        pstat = PStatCollector(collector_name)
        global_showbase.custom_collectors = {}
        global_showbase.custom_collectors[collector_name] = pstat

    def do_pstat(*args, **kargs):
        pstat.start()
        returned = func(*args, **kargs)
        pstat.stop()
        return returned

    do_pstat.__name__ = func.__name__
    do_pstat.__dict__ = func.__dict__
    do_pstat.__doc__ = func.__doc__
    return do_pstat
