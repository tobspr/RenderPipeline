
from direct.stdpy.file import open

from ..Util.DebugObject import DebugObject
from ..Util.ShaderUBO import ShaderUBO
from .DayTimeInterface import DayTimeInterface

class DayTimeManager(DebugObject):

    """ This is a wrapper arround the day time interface used by the pipeline """

    def __init__(self, pipeline):
        DebugObject.__init__(self)
        self._pipeline = pipeline
        self._interface = DayTimeInterface(self._pipeline.get_plugin_mgr().get_interface())
        self._settings = {}
        self._ubo = ShaderUBO("TimeOfDay")

    def load_settings(self):
        """ Loads the daytime settings """
        self.debug("Loading Time of Day settings ..")
        self._interface.set_base_dir(".")
        self._interface.load()

        for plugin in self._pipeline.get_plugin_mgr().get_interface().get_plugin_instances():
            for setting, handle in plugin.get_config().get_daytime_settings().items():
                setting_id = plugin.get_id() + "." + setting
                self._settings[setting_id] = handle
                self._ubo.register_pta(setting_id, handle.get_glsl_type())
                
        self._generate_shader_config()
        self._register_shader_inputs()

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
