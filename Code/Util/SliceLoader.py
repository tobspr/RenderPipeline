

from panda3d.core import PNMImage, VirtualFileSystem, VirtualFileMountRamdisk
from panda3d.core import Loader

class SliceLoader:

    @classmethod
    def load_3d_texture(cls, fname, slice_size):
        """ Loads a sliced 3D texture, assumes all slices have the same x, y
        and z-Size. """

        # Load sliced image from disk
        source = PNMImage(fname)
        w, h = source.get_x_size(), source.get_y_size()

        # Find slice properties
        num_cols = w // slice_size
        temp = PNMImage(slice_size, slice_size,
            source.get_num_channels(), source.get_maxval())

        # Construct a ramdisk to write the files to
        vfs = VirtualFileSystem.get_global_ptr()
        ramdisk = VirtualFileMountRamdisk()
        vfs.mount(ramdisk, "$$SliceLoaderTemp/", 0)

        # Extract all slices and write them to the virtual disk
        for z_slice in range(slice_size):
            slice_x = (z_slice % num_cols) * slice_size
            slice_y = (z_slice // num_cols) * slice_size
            temp.copy_sub_image(source, 0, 0, slice_x, slice_y, slice_size, slice_size)
            temp.write("$$SliceLoaderTemp/" + str(z_slice) + ".png")

        # Load the de-sliced texture from the ramdisk
        texture_handle = loader.load3DTexture("$$SliceLoaderTemp/#.png")

        # This should never trigger, but can't hurt to have
        assert(texture_handle.get_x_size() == slice_size)
        assert(texture_handle.get_y_size() == slice_size)
        assert(texture_handle.get_z_size() == slice_size)

        # Finally unmount the ramdisk
        vfs.unmount(ramdisk)
        
        return texture_handle
        
if __name__ == "__main__":

    """ Testing script """

    import direct.directbase.DirectStart

    SliceLoader.load_3d_texture(
        "../../Plugins/ColorCorrection/Resources/DefaultLUT.png", 64)


