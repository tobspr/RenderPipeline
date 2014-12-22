from direct.stdpy.file import isfile, open
from DebugObject import DebugObject

from panda3d.core import Vec3

class SettingsManager(DebugObject):

    """ This class is a base class for loading settings from
    ini files. Subclasses should implement _addDefaultSettings.
    Settings can be queried using the [] operator, saving is
    currently not supported. To load a ini file, loadFromFile
    has to be called.
    """

    class Setting:

        """ This is a subclass used by the SettingsManager. Each setting
        is stored via a instance of this class. This class store the name,
        type and default-value of a property. Also it handles the casting
        of strings to the desired type """

        def __init__(self, name, sType, default):
            """ Constructs a new Setting. sType should be a generic type,
            like int, bool, str. """

            self.name = name
            self.type = sType
            self.default = default
            self.value = self.default

        def setValue(self, val):
            """ Attempts to set the current value to val. When the value is not
            castable, the current value is set to the default value """

            try:
                # Extra check for bools, as a string always is true when
                # non-zero
                if self.type == bool:
                    val = val.lower()
                    if val not in ["true", "false"]:
                        return False
                    self.value = val == "true"

                # Special check for vectors
                elif self.type == Vec3:

                    values = [float(i) for i in val.strip().split(";")]
                    if len(values) != 3:
                        return False

                    self.value = Vec3(*values)

                # Strings may use '"'
                elif self.type == str:
                    self.value = self.type(val).strip('"')

                else:
                    self.value = self.type(val)

            except:
                self.value = self.default
                return False

            return True

        def getValue(self):
            """ Returns the current value """

            return self.value

    def __init__(self, name):
        """ Creates a new settings manager. Subclasses should implement
        _addDefaultSettings to populate the settings. Otherwise this class
        won't be able to read the options. With loadFromFile a ini file is
        read, and the settings are filled with values from it. """

        DebugObject.__init__(self, name)
        self.settings = {}
        self._addDefaultSettings()

    def _addSetting(self, name, sType, default):
        """ Internal shortcut to add a setting to the list of supported
        settings """

        self.settings[name] = self.Setting(name, sType, default)

    def _addDefaultSettings(self):
        """ Child classes have to implement this. """

        raise NotImplementedError()

    def loadFromFile(self, filename):
        """ Attempts to load settings from a given file. When the file
        does not exist, nothing happens, and an error is printed """

        self.debug("Loading ini-file from", filename)

        if not isfile(filename):
            self.error("File not found:", filename)
            return

        handle = open(filename, "r")
        content = handle.readlines()
        handle.close()

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
            settingName = parts[0].strip()
            settingValue = ""

            if len(parts) > 1:
                settingValue = parts[1].strip()

            if settingName not in self.settings:
                self.warn("Unrecognized setting:", settingName)
                continue

            self.settings[settingName].setValue(settingValue)
            setattr(self, settingName, self.settings[settingName].getValue())

    # def __getitem__(self, name):
        # """ This function makes accessing the settings via [] possible.
        # Throws an exception when the setting does not exist. """
        
        # if name in self.settings:
        #     return self.settings[name].getValue()
        # else:
        #     raise Exception("The setting '" + str(name) + "' does not exist")

