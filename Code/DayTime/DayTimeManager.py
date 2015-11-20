
from direct.stdpy.file import open

from ..Util.DebugObject import DebugObject
from ..Util.ShaderUBO import ShaderUBO
from .DayTimeInterface import DayTimeInterface

class DayTimeManager(DebugObject):

    """ This is a wrapper arround the day time interface used by the pipeline """

    def __init__(self, pipeline):
        DebugObject.__init__(self)
        self._pipeline = pipeline
        self._interface = DayTimeInterface(
            self._pipeline.get_plugin_mgr().get_interface())
        self._interface.set_base_dir(".")
        self._settings = {}
        self._ubo = ShaderUBO("TimeOfDay")
        self._daytime = 0.4

    def load_settings(self):
        """ Loads the daytime settings """
        self.debug("Loading Time of Day settings ..")
        self._interface.load()

        for plugin in self._pipeline.get_plugin_mgr().get_interface().get_plugin_instances():
            for setting, handle in plugin.get_config().get_daytime_settings().items():
                setting_id = plugin.get_id() + "." + setting
                self._settings[setting_id] = handle
                self._ubo.register_pta(setting_id, handle.get_glsl_type())
                
        self._generate_shader_config()
        self._register_shader_inputs()

    def reload_config(self):
        """ Reloads the daytime config """
        self.debug("Reloading daytime config ..")
        self._interface.load()

    def set_time(self, t):
        """ Sets the current time of day """
        self._daytime = t

    def update(self):
        """ Updates all the daytime inputs """
        for setting_name, handle in self._settings.items():    
            setting_value = handle.get_scaled_value(self._daytime)
            self._ubo.update_input(setting_name, setting_value)

    def get_setting_value(self, plugin, setting):
        """ Returns the current value of a setting """
        key = plugin + "." + setting
        if key not in self._settings:
            self.warn("Setting not found:", plugin,"->", setting)
            return None
        return self._settings[key].get_value(self._daytime)

    def _register_shader_inputs(self):
        """ Registers the daytime pta's to the stage manager """
        self._pipeline.get_stage_mgr().add_ubo(self._ubo)

    def _generate_shader_config(self):
        """ Generates the shader configuration """
        content = self._ubo.generate_shader_code()

        # Try to write the temporary file
        try:
            with open("$$PipelineTemp/$$DayTimeConfig.inc.glsl", "w") as handle:
                handle.write(content)
        except IOError as msg:
            self.error("Failed to write daytime autoconfig!", msg)
