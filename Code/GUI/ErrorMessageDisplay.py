
from __future__ import print_function

from panda3d.core import Notify, LineStream, Vec3

from ..Globals import Globals
from ..Util.DebugObject import DebugObject

from .BetterOnscreenText import BetterOnscreenText

class ErrorMessageDisplay(DebugObject):

    """ This is a gui element which listens to the panda output stream
    and shows errors """

    def __init__(self):
        DebugObject.__init__(self)
        self._num_errors = 0
        self._error_node = Globals.base.pixel2d.attach_new_node("ErrorDisplay")
        self._notify_stream = None

    def _init_notify(self):
        """ Internal method to init the stream to catch all notify messages """
        self._notify_stream = LineStream()
        Notify.ptr().set_ostream_ptr(self._notify_stream, False)

    def update(self):
        """ Updates the error display, fetching all new messages from the notify
        stream """

        # Disabled for now
        return

        if not self._notify_stream:
            self._init_notify()

        while self._notify_stream.is_text_available():
            line = self._notify_stream.get_line().strip()
            print(line)
            self.add_error(line)

    def add_error(self, msg):
        """ Adds a new error message """

        BetterOnscreenText(
            x=Globals.base.win.get_x_size() - 30,
            y=Globals.base.win.get_y_size() - 30 + self._num_errors * 30,
            align="right", text=msg, color=Vec3(1, 0.1, 0.1), size=15,
            parent=self._error_node)

        self._error_node.set_z(self._num_errors * 30)
        self._num_errors += 1

        if self._num_errors > 100:
            self.clear_messages()
            self.add_error("Error count exceeded. Cleared errors ..")

    def clear_messages(self):
        """ Clears all messages / removes them """
        self._error_node.node().remove_all_children()
        self._num_errors = 0
        self._error_node.set_z(0)
