

from panda3d.core import Vec3
from direct.stdpy.file import isfile, open

from .DebugObject import DebugObject
from ..External.PyYAML import YAMLEasyLoad

class SettingsLoader(DebugObject):

    """ This class is a base class for loading settings from yaml files.
    Settings can be accessed as attributes, saving is currently not supported. 
    To load a yaml file, load_from_file has to be called.
    """

    def __init__(self, pipeline, name):
        DebugObject.__init__(self, name)
        self._pipeline = pipeline
        self._settings = {}
        self._file_loaded = False

    def is_file_loaded(self):
        """ Returns whether the settings were loaded from a file, otherwise
        the settings will be the default settings """
        return self._file_loaded

    def __getitem__(self, item_name):
        """ Returns a setting by name """
        if item_name not in self._settings:
            self.error("Could not find setting",item_name)
            return False
        return self._settings[item_name]

    def __setitem__(self, key, val):
        """ Adjust a setting """
        assert key in self._settings
        self._settings[key] = val

    def load_from_file(self, filename):
        """ Attempts to load settings from a given file. When the file
        does not exist, nothing happens, and an error is printed """

        self.debug("Loading settings-file from", filename)

        if not isfile(filename):
            self.error("File not found:", filename)
            return

        # Load actual settings file
        parsed_yaml = YAMLEasyLoad(filename)
        self._file_loaded = True

        if "settings" not in parsed_yaml:
            self.error("Missing root entry in settings file:", filename)
            return False

        # Flatten the recursive structure into a single dictionary
        def flatten_and_insert(root, prefix):
            for key, val in root.items():
                if isinstance(val, dict):
                    flatten_and_insert(val, prefix + key + ".")
                else:
                    self._settings[prefix + key] = val

        flatten_and_insert(parsed_yaml["settings"], "")
        self.debug("Loaded", len(self._settings), "settings")
