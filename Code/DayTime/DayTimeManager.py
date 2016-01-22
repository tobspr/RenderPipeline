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

from __future__ import division
from six import iteritems

from direct.stdpy.file import open

from ..Util.DebugObject import DebugObject
from ..Util.ShaderUBO import ShaderUBO
from .DayTimeInterface import DayTimeInterface
from ..BaseManager import BaseManager


class DayTimeManager(BaseManager):

    """ This is a wrapper arround the day time interface used by the pipeline """

    def __init__(self, pipeline):
        BaseManager.__init__(self)
        self._pipeline = pipeline
        self._interface = DayTimeInterface(
            self._pipeline.plugin_mgr.get_interface())
        self._interface.set_base_dir(".")
        self._settings = {}
        self._ubo = ShaderUBO("TimeOfDay")
        self._daytime = 0.5

    def load_settings(self):
        """ Loads the daytime settings """
        self.debug("Loading Time of Day settings ..")
        self._interface.load()

        for plugin in self._pipeline.plugin_mgr.get_interface().get_plugin_instances():
            for setting, handle in iteritems(plugin.get_config().get_daytime_settings()):
                setting_id = plugin.get_id() + "." + setting
                self._settings[setting_id] = handle
                self._ubo.register_pta(setting_id, handle.get_glsl_type())


        self._generate_shader_config()
        self._register_shader_inputs()

    def reload_config(self):
        """ Reloads the daytime config """
        self.debug("Reloading daytime config ..")
        self._interface.load()

    def set_time(self, daytime):
        """ Sets the current time of day, should be a float from 0 to 1, whereas
        0 denotes 0:00 and 1 denotes 24:00 """
        self._daytime = daytime

    def get_time_str(self):
        """ Returns the current time as string """
        total_minutes = int(self._daytime * 24 * 60)
        hour = total_minutes // 60
        minute =  total_minutes % 60
        return "{:02d}:{:02d}".format(hour, minute)

    def get_time(self):
        """ Returns the current time as float from 0 .. 1 """
        return self._daytime

    def get_num_constraints(self):
        """ Returns teh amount of constraints """
        return len(self._settings)

    def do_update(self):
        """ Updates all the daytime inputs """
        for setting_name, handle in iteritems(self._settings):
            setting_value = handle.get_scaled_value(self._daytime)
            self._ubo.update_input(setting_name, setting_value)

    def get_setting_value(self, plugin, setting):
        """ Returns the current value of a setting """
        key = plugin + "." + setting
        if key not in self._settings:
            self.warn("Setting not found:", plugin, "->", setting)
            return None
        return self._settings[key].get_value(self._daytime)

    def _register_shader_inputs(self):
        """ Registers the daytime pta's to the stage manager """
        self._pipeline.stage_mgr.add_ubo(self._ubo)

    def _generate_shader_config(self):
        """ Generates the shader configuration """
        content = self._ubo.generate_shader_code()

        # Try to write the temporary file
        try:
            with open("$$PipelineTemp/$$DayTimeConfig.inc.glsl", "w") as handle:
                handle.write(content)
        except IOError as msg:
            self.error("Failed to write daytime autoconfig!", msg)
