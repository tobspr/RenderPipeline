
from six.moves import range

import time

from panda3d.core import PNMImage, VirtualFileSystem, VirtualFileMountRamdisk

from ..Globals import Globals

class SliceLoader(object):

    """ Utility class to load 3D textures from a sliced 2D texture, since
    Panda does not support that. """

    def __init__(self):
        raise NotImplementedError("Class is a singleton.")

    @classmethod
    def load_3d_texture(cls, fname, tile_size_x, tile_size_y=None, num_tiles=None):
        """ Loads a texture from the given filename and dimensions. If only
        one dimensions is specified, the other dimensions are assumed to be
        equal. This internally loads the texture into ram, splits it into smaller
        sub-images, and then calls the load_3d_texture from the Panda loader """

        # Generate a unique name to prevent caching
        tempfile_name = "$$SliceLoaderTemp-" + str(time.time()) + "/"

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
        texture_handle = Globals.loader.load3DTexture(tempfile_name + "/#.png")

        # This should never trigger, but can't hurt to have
        assert texture_handle.get_x_size() == tile_size_x
        assert texture_handle.get_y_size() == tile_size_y
        assert texture_handle.get_z_size() == num_tiles

        # Finally unmount the ramdisk
        vfs.unmount(ramdisk)

        return texture_handle
