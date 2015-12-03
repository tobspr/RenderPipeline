

from .DebugObject import DebugObject
from .UDPListenerService import UDPListenerService

class NetworkUpdateListener(DebugObject):

    """ Listener which listens on several ports for incoming updates """

    def __init__(self, pipeline):
        DebugObject.__init__(self)
        self._pipeline = pipeline
        self._config_updates = set()
        self._daytime_updates = set()

    def setup(self):
        """ Starts the listener threads """
        self._fix_showbase_shutdown()

        UDPListenerService.listener_thread(
            UDPListenerService.CONFIG_PORT, self._on_config_msg)
        UDPListenerService.listener_thread(
            UDPListenerService.DAYTIME_PORT, self._on_daytime_msg)

    def _on_config_msg(self, msg):
        """ Internal handler when a config message arrived """
        self._config_updates.add(msg)

    def _on_daytime_msg(self, msg):
        """ Internal handler when a dytime message arrived """
        self._daytime_updates.add(msg)

    def update(self):
        """ Update task which gets called every frame and executes the changes"""

        # Config updates
        if self._config_updates:
            update = self._config_updates.pop()
            self._pipeline.get_plugin_mgr().on_setting_change(update)
        elif self._daytime_updates:
            cmd = self._daytime_updates.pop()
            self._handle_daytime_command(cmd)

    def _handle_daytime_command(self, cmd):
        """ Handles a daytime command """
        if cmd.startswith("settime "):
            daytime = float(cmd.split()[1])
            self._pipeline.get_daytime_mgr().set_time(daytime)
        elif cmd.startswith("loadconf"):
            self._pipeline.get_plugin_mgr().reload_settings()
            self._pipeline.get_daytime_mgr().reload_config()
        else:
            self.warn("Recieved unkown daytime command:", cmd)

    def _fix_showbase_shutdown(self):
        """ Fixes the showbase run method to properly stop all threads
        after the showbase got closed """
        old_run = self._pipeline._showbase.run
        def new_run(*args):
            try:
                old_run(*args)
            except SystemExit as msg:
                pass

            # Todo: maybe just stop the thread instead of shutting
            # everything down
            import os
            os._exit(0)

        self._pipeline._showbase.run = new_run
        