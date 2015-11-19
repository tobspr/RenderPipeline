
"""

This tool offers an interface to configure the time of day settings

"""

from __future__ import print_function
import sys
import time
from functools import partial

# Add the render pipeline to the path
sys.path.insert(0, "../../")

# Load all PyQt classes
try:
    import PyQt4.QtCore as QtCore 
    import PyQt4.QtGui as QtGui
except ImportError as msg:
    print("Failed to import PyQt4:", msg)
    print("Please make sure you installed PyQt!")
    sys.exit(1)

from ui.main_window_generated import Ui_MainWindow
from CurveWidget import CurveWidget
from Code.DayTime.DayTimeManager import DayTimeManager
from Code.PluginInterface.Virtual.VirtualPluginInterface import VirtualPluginInterface

connect = QtCore.QObject.connect


class DayTimeEditor(QtGui.QMainWindow, Ui_MainWindow):

    """ This is the main editor class which handles the user interface """

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi()

        # Construct a new virtual interface since we don't run in the pipeline
        self._interface = VirtualPluginInterface()
        self._interface.load_plugin_config()
        self._interface.load_plugins()

        # Construct a new daytime manager with that interface
        self._daytime = DayTimeManager(self._interface)
        self._daytime.load()

        self._update_settings_list()

        self._selected_setting_handle = None
        self._selected_setting = None
        self._selected_plugin = None
        self._on_time_changed(self.time_slider.value())
        self.set_settings_visible(False)

    def set_settings_visible(self, visibility):
        if not visibility:
            self.frame_current_setting.hide()
            self.lbl_select_setting.show()
        else:
            self.frame_current_setting.show()
            self.lbl_select_setting.hide()

    def setupUi(self):
        """ Setups the UI Components """
        Ui_MainWindow.setupUi(self, self)
        self.settings_tree.setColumnWidth(0, 200)
        self.settings_tree.expandAll()

        self.edit_widget = CurveWidget(self)
        self.prefab_edit_widget.addWidget(self.edit_widget)

        connect(self.time_slider, QtCore.SIGNAL("valueChanged(int)"), self._on_time_changed)

        connect(self.settings_tree, QtCore.SIGNAL("itemSelectionChanged()"), self._on_setting_selected)

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
            self.lbl_plugin_src.setText("Plugin: " + self._selected_plugin)
            self.lbl_setting_desc.setText("Description: " + self._selected_setting_handle.description)

            self.edit_widget.set_curves(self._selected_setting_handle.curves)
            self.set_settings_visible(True)

    def _on_time_changed(self, val):
        """ Handler when the time slider got moved """
        hour = val / (60 * 60 * 60)
        minute = (val / (60 * 60)) % 60
        ftime = float(val) / (24 * 60 * 60 * 60)

        self.time_label.setText(str(hour).zfill(2) + ":" + str(minute).zfill(2))
        self.edit_widget.set_current_time(ftime)

    def _update_settings_list(self):
        """ Updates the list of visible settings """

        self.settings_tree.clear()

        for plugin in self._interface.get_plugin_instances():

            if not self._interface.is_plugin_enabled(plugin.get_id()):
                continue
                
            daytime_settings = plugin.get_config().get_daytime_settings()
            
            if not daytime_settings:
                # Skip plugins with empty settings
                continue

            plugin_head = QtGui.QTreeWidgetItem(self.settings_tree)                
            plugin_head.setText(0, plugin.get_name())
            plugin_head.setFlags(QtCore.Qt.ItemIsEnabled)

            # Display all settings
            for setting, setting_handle in daytime_settings.items():

                setting_item = QtGui.QTreeWidgetItem(plugin_head)
                setting_item.setText(0, setting_handle.label)
                setting_item.setText(1, setting_handle.format(setting_handle.default))
                setting_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                setting_item._setting_id = setting
                setting_item._setting_handle = setting_handle
                setting_item._plugin_id = plugin.get_id()

        self.settings_tree.expandAll()

# Start application
app = QtGui.QApplication(sys.argv)
editor = DayTimeEditor()
editor.show()
app.exec_()
