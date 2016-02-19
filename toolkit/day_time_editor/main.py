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

# This tool offers an interface to configure the time of day settings


from __future__ import print_function

import os
import sys
import time
from functools import partial
from threading import Thread

# Change to the current directory
os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__))))

# Add the render pipeline to the path
sys.path.insert(0, "../../")

from rplibs.six import iteritems

# Load all PyQt classes
try:
    import PyQt4.QtCore as QtCore
    import PyQt4.QtGui as QtGui
except ImportError as msg:
    print("Failed to import PyQt4:", msg)
    print("Please make sure you installed PyQt!")
    sys.exit(1)

from curve_widget import CurveWidget

from ui.main_window_generated import Ui_MainWindow
from rpcore.pluginbase.manager import PluginManager
from rpcore.mount_manager import MountManager
from rpcore.util.udp_listener_service import UDPListenerService

connect = QtCore.QObject.connect

class DayTimeEditor(QtGui.QMainWindow, Ui_MainWindow):

    """ This is the main editor class which handles the user interface """

    def __init__(self):

        # Init mounts
        self._mount_mgr = MountManager(None)
        self._mount_mgr.mount()

        self._plugin_mgr = PluginManager(None)
        self._plugin_mgr.load()

        QtGui.QMainWindow.__init__(self)
        self.setupUi()
        self._tree_widgets = []
        self._cmd_queue = set()

        self._update_settings_list()

        self._selected_setting_handle = None
        self._selected_setting = None
        self._selected_plugin = None
        self._current_time = 0.5
        self._on_time_changed(self.time_slider.value())
        self.set_settings_visible(False)

        self._bg_thread = Thread(target=self.updateThread)
        self._bg_thread.start()

    def set_settings_visible(self, visibility):
        if not visibility:
            self.frame_current_setting.hide()
            self.lbl_select_setting.show()
        else:
            self.frame_current_setting.show()
            self.lbl_select_setting.hide()

    def closeEvent(self, event):
        event.accept()
        import os
        os._exit(1)

    def updateThread(self):
        """ Seperate update thread """

        while True:
            if self._cmd_queue:
                cmd = self._cmd_queue.pop()
                if cmd == "settime":
                    local_time = self._current_time
                    UDPListenerService.ping(UDPListenerService.DAYTIME_PORT, "settime " + str(local_time))

                elif cmd == "write_settings":
                    self._plugin_mgr.save_daytime_overrides("$$config/daytime.yaml")
                    UDPListenerService.ping(UDPListenerService.DAYTIME_PORT, "loadconf")
                else:
                    print("Unkown cmd:", cmd)

            time.sleep(0.1)

    def setupUi(self):
        """ Setups the UI Components """
        Ui_MainWindow.setupUi(self, self)
        self.settings_tree.setColumnWidth(0, 160)
        self.settings_tree.expandAll()

        self.edit_widget = CurveWidget(self)
        self.edit_widget.set_change_handler(self._on_curve_edited)
        self.prefab_edit_widget.addWidget(self.edit_widget)

        connect(self.time_slider,QtCore.SIGNAL("valueChanged(int)"), self._on_time_changed)
        connect(self.settings_tree, QtCore.SIGNAL("itemSelectionChanged()"), self._on_setting_selected)

    def _update_tree_widgets(self):
        """ Updates the tree widgets """
        for setting_handle, widget in self._tree_widgets:
            value = setting_handle.get_scaled_value_at(self._current_time)
            formatted = setting_handle.format(value)
            widget.setText(1, formatted)

            if setting_handle.type == "color":
                widget.setBackground(1, QtGui.QBrush(QtGui.QColor(*value)))

    def _on_curve_edited(self):
        """ Called when the curve got edited in the curve widget """
        self._cmd_queue.add("write_settings")
        self._update_tree_widgets()

    def _on_setting_selected(self):
        """ Called when a setting got selected in the settings tree """
        selected = self.settings_tree.selectedItems()
        if len(selected) != 1:
            self._selected_setting = None
            self._selected_plugin = None
            self._selected_setting_handle = None
            self.edit_widget.set_curves([])
            self.set_settings_visible(False)
        else:
            selected = selected[0]

            self._selected_plugin = selected._plugin_id
            self._selected_setting = selected._setting_id
            self._selected_setting_handle = selected._setting_handle

            self.lbl_current_setting.setText(self._selected_setting_handle.label)
            self.lbl_setting_desc.setText(self._selected_setting_handle.description)

            self.edit_widget.set_curves(self._selected_setting_handle.curves)

            if self._selected_setting_handle.type == "color":
                self.edit_widget.set_unit_processor(lambda x: str(int(x * 255)))
            else:
                self.edit_widget.set_unit_processor(lambda x:self._selected_setting_handle.format(self._selected_setting_handle.get_scaled_value(x)))

            self.set_settings_visible(True)
            self._update_tree_widgets()

    def _on_time_changed(self, val):
        """ Handler when the time slider got moved """
        hour = val / (60 * 60 * 60)
        minute = (val / (60 * 60)) % 60
        ftime = float(val) / (24 * 60 * 60 * 60)

        self.time_label.setText(str(hour).zfill(2) + ":" + str(minute).zfill(2))
        self.edit_widget.set_current_time(ftime)
        self._current_time = ftime
        self._update_tree_widgets()
        self._cmd_queue.add("settime")

    def _update_settings_list(self):
        """ Updates the list of visible settings """

        self.settings_tree.clear()
        self._tree_widgets = []

        for plugin_id, plugin in iteritems(self._plugin_mgr.plugin_instances):

            if not self._plugin_mgr.is_plugin_enabled(plugin_id):
                continue

            daytime_settings = self._plugin_mgr.day_settings[plugin_id]

            if not daytime_settings:
                # Skip plugins with empty settings
                continue

            plugin_head = QtGui.QTreeWidgetItem(self.settings_tree)
            plugin_head.setText(0, plugin.name)
            plugin_head.setFlags(QtCore.Qt.ItemIsEnabled)

            # Display all settings
            for setting, setting_handle in iteritems(daytime_settings):
                setting_item = QtGui.QTreeWidgetItem(plugin_head)
                setting_item.setText(0, setting_handle.label)
                setting_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                setting_item._setting_id = setting
                setting_item._setting_handle = setting_handle
                setting_item._plugin_id = plugin_id
                setting_item.setToolTip(0, setting_handle.description)
                setting_item.setToolTip(1, setting_handle.description)
                self._tree_widgets.append((setting_handle, setting_item))

        self.settings_tree.expandAll()

# Start application
app = QtGui.QApplication(sys.argv)
editor = DayTimeEditor()
editor.show()
app.exec_()
