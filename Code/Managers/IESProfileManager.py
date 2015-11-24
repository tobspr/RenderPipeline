
from panda3d.core import Filename, Texture

from ..Util.DebugObject import DebugObject
from ..Util.IESProfileLoader import IESProfileLoader, IESLoaderException

class IESProfileManager(DebugObject):

    """ Manager which handles the different IES profiles, and also handles
    loading .IES files """

    def __init__(self, pipeline):
        DebugObject.__init__(self)
        self._pipeline = pipeline
        self._entries = []
        self._loader = IESProfileLoader()
        self._max_entries = 32
        self._create_storage()

    def _create_storage(self):
        """ Internal method to create the storage for the profile dataset textures """
        self._storage_tex = Texture("IESDatasets")
        self._storage_tex.setup_3d_texture(512, 512, self._max_entries, Texture.T_float, Texture.F_r16)        
        self._storage_tex.set_minfilter(Texture.FT_linear)
        self._storage_tex.set_magfilter(Texture.FT_linear)
        self._storage_tex.set_wrap_u(Texture.WM_clamp)
        self._storage_tex.set_wrap_v(Texture.WM_clamp)
        self._storage_tex.set_wrap_w(Texture.WM_clamp)

    def load(self, filename):
        """ Loads a profile from a given filename """

        # Make filename unique
        f = Filename.from_os_specific(filename)
        f.make_absolute()
        f = f.get_fullpath()

        # Check for cache entries
        if f in self._entries:
            return self._entries.index(f)

        # Check for out of bounds
        # TODO: Could remove unused profiles or regenerate texture
        if len(self._entries) >= self._max_entries:
            self.warn("Cannot load IES Profile, too many loaded! (Maximum: 32)")

        # Try loading the dataset, and see what happes
        try:
            dataset = self._loader.load(f)
        except IESLoaderException as msg:
            self.warn("Failed to load profile from",filename, ":", msg)
            return -1

        if not dataset:
            return -1

        # Dataset was loaded successfully, now copy it
        dataset.generate_dataset_texture_into(self._storage_tex, len(self._entries), 512, 512)
        self._entries.append(f)

        return len(self._entries) - 1
