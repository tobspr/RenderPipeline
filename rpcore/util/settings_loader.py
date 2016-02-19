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
from six import iteritems

from direct.stdpy.file import isfile

from ..rp_object import RPObject
from rplibs.yaml import load_yaml_file

class SettingsLoader(RPObject):

    """ This class is a base class for loading settings from yaml files.
    Settings can be accessed as attributes, saving is currently not supported.
    To load a yaml file, load_from_file has to be called.
    """

    def __init__(self, pipeline, name):
        RPObject.__init__(self, name)
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
            self.error("Could not find setting", item_name)
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
        parsed_yaml = load_yaml_file(filename)
        self._file_loaded = True

        if "settings" not in parsed_yaml:
            self.error("Missing root entry in settings file:", filename)
            return False

        # Flatten the recursive structure into a single dictionary
        def flatten_and_insert(root, prefix):
            for key, val in iteritems(root):
                if isinstance(val, dict):
                    flatten_and_insert(val, prefix + key + ".")
                else:
                    self._settings[prefix + key] = val

        flatten_and_insert(parsed_yaml["settings"], "")
        self.debug("Loaded", len(self._settings), "settings")
