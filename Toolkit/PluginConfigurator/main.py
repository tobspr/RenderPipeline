
"""

This tool offers an interface to configure the pipeline

"""

from __future__ import print_function
import sys
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

# Load the generated UI Layout
from ui.main_window_generated import Ui_MainWindow

from Source.PluginInterface import PluginInterface
from Code.Util.UDPListenerService import UDPListenerService

connect = QtCore.QObject.connect

class PluginConfigurator(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self._interface = PluginInterface()
        self._current_plugin = None
        self._current_plugin_instance = None
        self.lbl_restart_pipeline.hide()
        self._set_settings_visible(False)

        connect(self.lst_plugins, QtCore.SIGNAL("itemSelectionChanged()"), self.on_plugin_selected)
        connect(self.lst_plugins, QtCore.SIGNAL("itemChanged(QListWidgetItem*)"), self.on_plugin_state_changed)

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
        assert(len(selected_item) == 1)
        selected_item = selected_item[0]
        self._current_plugin = selected_item._plugin_id
        self._current_plugin_instance = self._interface.get_plugin_by_id(self._current_plugin)
        assert(self._current_plugin_instance is not None)
        self._render_current_plugin()
        self._set_settings_visible(True)

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

        for index, (name, handle) in enumerate(settings.items()):

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
                label.setStyleSheet("background: rgba(200, 255, 200, 255);")

            label.setMargin(10)

            self.table_plugin_settings.setCellWidget(row_index, 0, label)

            item_default = QtGui.QTableWidgetItem()
            item_default.setText(str(handle.default))
            item_default.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table_plugin_settings.setItem(row_index, 1, item_default)

            setting_widget = self._get_widget_for_setting(name, handle)
            self.table_plugin_settings.setCellWidget(row_index, 2, setting_widget)

            item_desc = QtGui.QTableWidgetItem()
            item_desc.setText(handle.description)
            self.table_plugin_settings.setItem(row_index, 3, item_desc)

    def _do_update_setting(self, setting_id, value):
        # print("Update setting: ", setting_id, value)

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
            # print("Sending reload packet ...")
            # In case the setting is dynamic, notice the pipeline about it:
            UDPListenerService.ping_thread(UDPListenerService.DEFAULT_PORT, self._current_plugin + "." + setting_id)

        # Update GUI, but only in case of enum values, since they can trigger
        # display conditions:
        if setting_handle.type == "ENUM":
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
        widget.setLayout(layout)

        if setting.type == "BOOL":
            box = QtGui.QCheckBox()
            box.setChecked(QtCore.Qt.Checked if setting.value else QtCore.Qt.Unchecked)
            box.setStyleSheet("margin-left:30%;")
            connect(box, QtCore.SIGNAL("stateChanged(int)"), 
                partial(self._on_setting_bool_changed, setting_id))
            layout.addWidget(box)

        elif setting.type == "FLOAT" or setting.type == "INT":

            if setting.type == "FLOAT":
                box = QtGui.QDoubleSpinBox()
                
                if setting.max_value - setting.min_value < 1.0:
                    box.setDecimals(4)
            else:
                box = QtGui.QSpinBox()
            box.setMinimum(setting.min_value)
            box.setMaximum(setting.max_value)
            box.setValue(setting.value)
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

        return widget

    def _set_settings_visible(self, flag):
        """ Sets wheter the settings panel is visible or not """
        if flag:
            self.lbl_select_plugin.hide()
            self.frame_details.show()
        else:
            self.lbl_select_plugin.show()
            self.frame_details.hide()

    def _load_plugin_list(self):
        """ Reloads the whole plugin list """
        print("Loading plugin list")

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

