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


from .DebugObject import DebugObject
from .UDPListenerService import UDPListenerService
from ..BaseManager import BaseManager

class NetworkUpdateListener(BaseManager):

    """ Listener which listens on several ports for incoming updates """

    def __init__(self, pipeline):
        BaseManager.__init__(self)
        self._pipeline = pipeline
        self._config_updates = set()
        self._daytime_updates = set()

    def setup(self):
        """ Starts the listener threads """
        self._config_thread = UDPListenerService.listener_thread(
            UDPListenerService.CONFIG_PORT, self._on_config_msg)
        self._daytime_thread = UDPListenerService.listener_thread(
            UDPListenerService.DAYTIME_PORT, self._on_daytime_msg)

    def _on_config_msg(self, msg):
        """ Internal handler when a config message arrived """
        self._config_updates.add(msg)

    def _on_daytime_msg(self, msg):
        """ Internal handler when a dytime message arrived """
        self._daytime_updates.add(msg)

    def do_update(self):
        """ Update task which gets called every frame and executes the changes"""

        # Config updates
        if self._config_updates:
            update = self._config_updates.pop()
            self._pipeline.plugin_mgr.on_setting_change(update)
        elif self._daytime_updates:
            cmd = self._daytime_updates.pop()
            self._handle_daytime_command(cmd)

    def _handle_daytime_command(self, cmd):
        """ Handles a daytime command """
        if cmd.startswith("settime "):
            daytime = float(cmd.split()[1])
            self._pipeline.daytime_mgr.set_time(daytime)
        elif cmd.startswith("loadconf"):
            self._pipeline.plugin_mgr.reload_settings()
            self._pipeline.daytime_mgr.reload_config()
        else:
            self.warn("Recieved unkown daytime command:", cmd)
