

from panda3d.core import Vec3
from direct.stdpy.file import isfile, open

from .DebugObject import DebugObject


class SettingsLoader(DebugObject):

    """ This class is a base class for loading settings from ini files.
    Subclasses should implement _addDefaultSettings. Settings can be accessed
    as attributes, saving is currently not supported. To load a ini file,
    load_from_file has to be called.
    """

    class Setting:

        """ This is a subclass used by the SettingsLoader. Each setting
        is stored via a instance of this class. This class store the name,
        type and default-value of a property. Also it handles the casting
        of strings to the desired type """

        def __init__(self, name, setting_type, default):
            """ Constructs a new Setting. setting_type should be a generic type,
            like int, bool, str. """

            self._name = name
            self._setting_type = setting_type
            self._default = default
            self._value = self._default

        def set_value(self, val):
            """ Attempts to set the current value to val. When the value is not
            castable, the current value is set to the default value """

            try:
                # Extra check for bools, as a string always is true when
                # non-zero
                if isinstance(self._setting_type, bool):
                    val = val.lower()
                    if val not in ["true", "false"]:
                        return False
                    self._value = val == "true"

                # Special check for vectors
                elif isinstance(self._setting_type, Vec3):
                    values = [float(i) for i in val.strip().split(";")]
                    if len(values) != 3:
                        return False
                    self._value = Vec3(*values)

                # Strings may use '"'
                elif isinstance(self._setting_type, str):
                    self._value = self._setting_type(val).strip('"\'')

                # Otherwise just cast the type
                else:
                    self._value = self._setting_type(val)
            except:
                self._value = self._default
                return False
            return True

        def get_value(self):
            """ Returns the current value """
            return self._value

        def reset_to_default(self):
            """ Resets the value to the default value """
            self._value = self._default

        def get_default(self):
            """ Returns the default value of the setting """
            return self._default

    def __init__(self, name, pipeline):
        """ Creates a new settings manager. Subclasses should implement
        _add_default_settings to populate the settings. Otherwise this class
        won't be able to read the options. With load_from_file an ini file is
        read, and the settings are filled with values from it. """
        DebugObject.__init__(self, name)
        self._settings = {}
        self._pipeline = pipeline
        self._file_loaded = False
        self._add_default_settings()

    def _add_setting(self, name, setting_type, default):
        """ Internal shortcut to add a setting to the list of supported
        settings. """
        self._settings[name] = self.Setting(name, setting_type, default)

    def _add_default_settings(self):
        """ Child classes have to implement this. """
        raise NotImplementedError()

    def is_file_loaded(self):
        """ Returns whether the settings were loaded from a file, otherwise
        the settings will be the default settings """
        return self._file_loaded

    def set_setting(self, key, val):
        """ Adjust a setting """
        assert key in self._settings
        self._settings[key].set_value(val)
        setattr(self, key, self._settings[key].get_value())

    def load_from_file(self, filename):
        """ Attempts to load settings from a given file. When the file
        does not exist, nothing happens, and an error is printed """

        self.debug("Loading ini-file from", filename)

        if not isfile(filename):
            self.error("File not found:", filename)
            return

        self._file_loaded = True
        with open(filename, "r") as handle:
            content = handle.readlines()

        # Set to default settings
        for name, setting in list(self._settings.items()):
            setting.set_value(setting.get_default())
            setattr(self, name, setting.get_default())

        # Read new settings
        for line in content:
            line = line.strip()

            # Empty line, comment, or section
            if len(line) < 1 or line[0] in ["//", "#", "["]:
                continue

            # No assignment
            if "=" not in line:
                self.warn("Ignoring invalid line:", line)
                continue

            parts = line.split("=")
            setting_name = parts[0].strip()
            setting_value = ""

            if len(parts) > 1:
                setting_value = parts[1].strip()

            if setting_name not in self._settings:
                self.warn("Unrecognized setting:", setting_name)
                continue

            self.set_setting(setting_name, setting_value)
