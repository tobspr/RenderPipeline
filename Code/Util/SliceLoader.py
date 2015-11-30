
import time

from panda3d.core import PNMImage, VirtualFileSystem, VirtualFileMountRamdisk
from panda3d.core import Loader

class SliceLoader:

    @classmethod
    def load_3d_texture(cls, fname, tile_size_x, tile_size_y=None, num_tiles=None):

        # Generate a unique name to prevent caching
        tempfile_name = "$$SliceLoaderTemp-" + str(time.time()) + "/"

        # For quaddratic textures
        tile_size_y = tile_size_x if tile_size_y is None else tile_size_y
        num_tiles = tile_size_x if num_tiles is None else num_tiles

        # Load sliced image from disk
        source = PNMImage(fname)
        w, h = source.get_x_size(), source.get_y_size()

        # Find slice properties
        num_cols = w // tile_size_x
        temp = PNMImage(tile_size_x, tile_size_y,
            source.get_num_channels(), source.get_maxval())

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
        texture_handle = loader.load3DTexture(tempfile_name + "/#.png")

        # This should never trigger, but can't hurt to have
        assert(texture_handle.get_x_size() == tile_size_x)
        assert(texture_handle.get_y_size() == tile_size_y)
        assert(texture_handle.get_z_size() == num_tiles)

        # Finally unmount the ramdisk
        vfs.unmount(ramdisk)
        
        return texture_handle

if __name__ == "__main__":

    """ Testing script """

    import direct.directbase.DirectStart

    SliceLoader.load_3d_texture(
        "../../Plugins/ColorCorrection/Resources/DefaultLUT.png", 64)


