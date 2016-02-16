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

# This tool offers an interface to configure the pipeline

from __future__ import print_function

import os
import sys
import time
from threading import Thread
from functools import partial


# Change to the current directory
os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__))))

# Append the current directory to the path
sys.path.insert(0, os.getcwd())

# Add the render pipeline to the path
sys.path.insert(0, "../../")
sys.path.insert(0, "../../rpcore/External/six")

from six import iteritems

# Load all PyQt classes
try:
    import PyQt4.QtCore as QtCore
    import PyQt4.QtGui as QtGui
except ImportError as msg:
    print("Failed to import PyQt4:", msg)
    print("Please make sure you installed PyQt!")
    sys.exit(1)

# Load the generated UI Layout
from ui.main_window_generated import Ui_MainWindow

from code.plugbase.virtual_plugbase import VirtualPluginInterface
from code.util.udp_listener_service import UDPListenerService
from code.mount_manager import MountManager

connect = QtCore.QObject.connect

class PluginConfigurator(QtGui.QMainWindow, Ui_MainWindow):

    """ Interface to change the plugin settings """

    def __init__(self):
        # Init mounts
        self._mount_mgr = MountManager(None)
        self._mount_mgr.mount()

        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self._interface = VirtualPluginInterface()
        self._current_plugin = None
        self._current_plugin_instance = None
        self.lbl_restart_pipeline.hide()
        self._set_settings_visible(False)
        self._update_queue = set()

        connect(self.lst_plugins, QtCore.SIGNAL("itemSelectionChanged()"), self.on_plugin_selected)
        connect(self.lst_plugins, QtCore.SIGNAL("itemChanged(QListWidgetItem*)"), self.on_plugin_state_changed)
        connect(self.btn_reset_plugin_settings, QtCore.SIGNAL("clicked()"), self.on_reset_plugin_settings)

        self._load_plugin_list()

        # Adjust column widths
        self.table_plugin_settings.setColumnWidth(0, 110)
        self.table_plugin_settings.setColumnWidth(1, 80)
        self.table_plugin_settings.setColumnWidth(2, 120)

        update_thread = Thread(target=self.update_thread, args=())
        update_thread.start()

    def closeEvent(self, event):
        event.accept()
        import os
        os._exit(1)

    def on_reset_plugin_settings(self):
        """ Gets called when the user wants to reset settings of a plugin """

        # Ask the user if he's really sure about it
        msg = "Are you sure you want to reset the settings of '" + self._current_plugin_instance.get_name() + "'?\n"
        msg+= "This does not reset the Time of Day settings of this plugin.\n\n"
        msg+= "!! This cannot be undone !! They will be lost forever (a long time!)."
        reply = QtGui.QMessageBox.question(self, "Warning",
                         msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:

            QtGui.QMessageBox.information(self, "Success", "Settings have been reset! You may have to restart the pipeline.")
            self._interface.reset_plugin_settings(self._current_plugin)

            # Save config
            self._interface.write_configuration()

            # Always show the restart hint, even if its not always required
            self._show_restart_hint()

            # Re-render everything
            self._load_plugin_list()

    def on_plugin_state_changed(self, item):
        plugin_id = item._plugin_id
        state = item.checkState() == QtCore.Qt.Checked
        self._interface.set_plugin_state(plugin_id, state)
        self._rewrite_plugin_config()
        self._show_restart_hint()

    def on_plugin_selected(self):
        """ Gets called when a plugin got selected in the plugin list """
        selected_item = self.lst_plugins.selectedItems()
        if not selected_item:
            self._current_plugin = None
            self._current_plugin_instance = None
            self._set_settings_visible(False)
            return
        assert(len(selected_item) == 1)
        selected_item = selected_item[0]
        self._current_plugin = selected_item._plugin_id
        self._current_plugin_instance = self._interface.get_plugin_handle(self._current_plugin)
        assert(self._current_plugin_instance is not None)
        self._render_current_plugin()
        self._set_settings_visible(True)

    def update_thread(self):
        while True:
            if len(self._update_queue) > 0:
                item = self._update_queue.pop()
                UDPListenerService.ping_thread(UDPListenerService.CONFIG_PORT, item)
            time.sleep(0.3)


    def _rewrite_plugin_config(self):
        """ Rewrites the plugin configuration """
        self._interface.write_configuration()

    def _render_current_plugin(self):
        """ Displays the currently selected plugin """
        self.lbl_plugin_name.setText(self._current_plugin_instance.get_name())

        version_str = "Version " + self._current_plugin_instance.get_config().get_version()
        version_str += " by " + self._current_plugin_instance.get_config().get_author()

        self.lbl_plugin_version.setText(version_str)
        self.lbl_plugin_desc.setText(self._current_plugin_instance.get_config().get_description())

        self._render_current_settings()

    def _show_restart_hint(self):
        """ Shows a hint to restart the pipeline """
        self.lbl_restart_pipeline.show()

    def _render_current_settings(self):
        """ Renders the current plugin settings """
        settings = self._current_plugin_instance.get_config().get_settings()

        # remove all rows
        while self.table_plugin_settings.rowCount() > 0:
            self.table_plugin_settings.removeRow(0)

        label_font = QtGui.QFont()
        label_font.setPointSize(10)
        label_font.setFamily("Segoe UI")

        desc_font = QtGui.QFont()
        desc_font.setPointSize(8)
        desc_font.setFamily("Segoe UI")

        for index, (name, handle) in enumerate(iteritems(settings)):

            # Dont show hidden settings
            if not handle.evaluate_display_conditions(settings):
                continue

            row_index = self.table_plugin_settings.rowCount()

            # Increase row count
            self.table_plugin_settings.insertRow(self.table_plugin_settings.rowCount())

            label = QtGui.QLabel()
            label.setText(handle.label)
            label.setWordWrap(True)
            label.setFont(label_font)

            if handle.is_dynamic():
                # label.setBackground(QtGui.QColor(200, 255, 200, 255))
                label.setStyleSheet("background: rgba(162, 204, 128, 255);")
            else:
                label.setStyleSheet("background: rgba(230, 230, 230, 255);")

            label.setMargin(10)

            self.table_plugin_settings.setCellWidget(row_index, 0, label)

            item_default = QtGui.QTableWidgetItem()
            item_default.setText(str(handle.default))
            item_default.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table_plugin_settings.setItem(row_index, 1, item_default)

            setting_widget = self._get_widget_for_setting(name, handle)
            self.table_plugin_settings.setCellWidget(row_index, 2, setting_widget)

            label_desc = QtGui.QLabel()
            label_desc.setText(handle.description)
            label_desc.setWordWrap(True)
            label_desc.setFont(desc_font)
            label_desc.setStyleSheet("color: #555;padding: 5px;")

            self.table_plugin_settings.setCellWidget(row_index, 3, label_desc)

    def _do_update_setting(self, setting_id, value):

        # Check whether the setting is a runtime setting
        setting_handle = self._current_plugin_instance.get_config().get_setting_handle(setting_id)

        # Skip the setting in case the value is equal
        if setting_handle.value == value:
            # print("Skipping setting")
            return

        # Otherwise set the new value
        setting_handle.set_value(value)

        self._interface.update_setting(self._current_plugin, setting_id, value)
        self._interface.write_configuration()

        if not setting_handle.is_dynamic():
            self._show_restart_hint()
        else:
            # In case the setting is dynamic, notice the pipeline about it:
            # print("Sending reload packet ...")
            self._update_queue.add(self._current_plugin + "." + setting_id)

        # Update GUI, but only in case of enum and bool values, since they can trigger
        # display conditions:
        if setting_handle.type == "ENUM" or setting_handle.type == "BOOL":
            self._render_current_settings()

    def _on_setting_bool_changed(self, setting_id, value):
        self._do_update_setting(setting_id, value == QtCore.Qt.Checked)

    def _on_setting_scalar_changed(self, setting_id, value):
        self._do_update_setting(setting_id, value)

    def _on_setting_enum_changed(self, setting_id, value):
        self._do_update_setting(setting_id, value)

    def _on_setting_slider_changed(self, setting_id, bound_objs, value):
        value /= 100000.0 # was stored packed
        self._do_update_setting(setting_id, value)

        for obj in bound_objs:
            obj.setValue(value)

    def _on_setting_spinbox_changed(self, setting_id, bound_objs, value):
        self._do_update_setting(setting_id, value)
        # Assume objects are sliders, so we need to rescale the value
        for obj in bound_objs:
            obj.setValue(value * 100000.0)

    def _get_widget_for_setting(self, setting_id, setting):
        """ Returns an appropriate widget to control the given setting """

        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignCenter)
        widget.setLayout(layout)

        if setting.type == "BOOL":
            box = QtGui.QCheckBox()
            box.setChecked(QtCore.Qt.Checked if setting.value else QtCore.Qt.Unchecked)
            connect(box, QtCore.SIGNAL("stateChanged(int)"),
                partial(self._on_setting_bool_changed, setting_id))
            layout.addWidget(box)

        elif setting.type == "FLOAT" or setting.type == "INT":

            if setting.type == "FLOAT":
                box = QtGui.QDoubleSpinBox()

                if setting.max_value - setting.min_value <= 2.0:
                    box.setDecimals(4)
            else:
                box = QtGui.QSpinBox()
            box.setMinimum(setting.min_value)
            box.setMaximum(setting.max_value)
            box.setValue(setting.value)

            box.setSingleStep( abs(setting.max_value - setting.min_value) / 100.0 )
            box.setAlignment(QtCore.Qt.AlignCenter)

            slider = QtGui.QSlider()
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.setMinimum(setting.min_value * 100000.0)
            slider.setMaximum(setting.max_value * 100000.0)
            slider.setValue(setting.value * 100000.0)

            layout.addWidget(box)
            layout.addWidget(slider)

            connect(slider, QtCore.SIGNAL("valueChanged(int)"),
                partial(self._on_setting_slider_changed, setting_id, [box]))

            value_type = "int" if setting.type == "INT" else "double"

            connect(box, QtCore.SIGNAL("valueChanged(" + value_type + ")"),
                partial(self._on_setting_spinbox_changed, setting_id, [slider]))

        elif setting.type == "ENUM":
            box = QtGui.QComboBox()
            for value in setting.values:
                box.addItem(value)
            connect(box, QtCore.SIGNAL("currentIndexChanged(QString)"),
                partial(self._on_setting_enum_changed, setting_id))
            box.setCurrentIndex(setting.values.index(setting.value))

            layout.addWidget(box)

        elif setting.type == "IMAGE":

            label = QtGui.QLabel()
            label.setText(setting.value)

            button = QtGui.QPushButton()
            button.setText("Choose File ...")
            connect(button, QtCore.SIGNAL("clicked()"), partial(self._choose_image, setting))

            layout.addWidget(label)
            layout.addWidget(button)

        return widget

    def _choose_image(self, setting_handle):
        """ Shows a file chooser to show an image from """

        filename = QtGui.QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png)")
        print("Filename =", filename)

    def _set_settings_visible(self, flag):
        """ Sets whether the settings panel is visible or not """
        if flag:
            self.lbl_select_plugin.hide()
            self.frame_details.show()
        else:
            self.lbl_select_plugin.show()
            self.frame_details.hide()

    def _load_plugin_list(self):
        """ Reloads the whole plugin list """
        print("Loading plugin list")

        # Reset selection
        self._current_plugin = None
        self._current_plugin_instance = None

        self._set_settings_visible(False)

        # Plugins are all plugins in the plugins directory
        self._interface.unload_plugins()
        self._interface.load_plugins()
        plugins = self._interface.get_plugin_instances()

        self.lst_plugins.clear()

        for plugin in plugins:
            item = QtGui.QListWidgetItem()
            item.setText(" " + plugin.get_name())

            if self._interface.is_plugin_enabled(plugin.get_id()):
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)

            item._plugin_id = plugin.get_id()
            self.lst_plugins.addItem(item)

# Start application
app = QtGui.QApplication(sys.argv)
configurator = PluginConfigurator()
configurator.show()
app.exec_()

