

from ..Util.DebugObject import DebugObject
from .DayTimeInterface import DayTimeInterface

class DayTimeManager(DebugObject):

    """ This is a wrapper arround the day time interface used by the pipeline """

    def __init__(self, pipeline):
        DebugObject.__init__(self)
        self._pipeline = pipeline
        self._interface = DayTimeInterface(self._pipeline.get_plugin_mgr().get_interface())
        self._settings = {}
        self._ptas = {}
        self._definitions = {}

    def load_settings(self):
        """ Loads the daytime settings """
        self.debug("Loading Time of Day settings ..")
        self._interface.set_base_dir(".")
        self._interface.load()

        for plugin in self._pipeline.get_plugin_mgr().get_interface().get_plugin_instances():
            self._definitions[plugin.get_id()] = {}
            for setting, handle in plugin.get_config().get_daytime_settings().items():
                setting_id = plugin.get_id() + "." + setting
                self._settings[setting_id] = handle
                self._ptas[setting_id] = handle.get_pta_type().empty_array(1)
                self._definitions[plugin.get_id()][setting] = handle.get_glsl_type()

        self._generate_shader_config()

    def _generate_shader_config(self):
        """ Generates the shader configuration """

        content = "#pragma once\n\n"

        content += "uniform struct {\n";

        for name, section in self._definitions.items():
            content += " "*4 + "struct {\n";
            for setting_id, glsl_type in section.items():
                content += " "*8 + glsl_type + " " + setting_id + ";\n"
            content += " "*4 + "} " + name + ";\n\n"

        content += "} TimeOfDay;\n\n"

        print(content)