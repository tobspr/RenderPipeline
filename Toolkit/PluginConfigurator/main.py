
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
        # self.lst_plugins.connect("onSelectionChanged()", self.on_plugin_selected)
        # self.lst_plugins.selectionChanged.connect(self.on_plugin_selected)
        # QtCore.QObject.connect(self.lst_plugins, QtCore.SIGNAL('selectionChanged()'), self.on_plugin_selected)

        # print(type(self.lst_plugins).selectionChanged)

        connect(self.lst_plugins, QtCore.SIGNAL("itemSelectionChanged()"), self.on_plugin_selected)
        connect(self.lst_plugins, QtCore.SIGNAL("itemChanged(QListWidgetItem*)"), self.on_plugin_state_changed)

        self._load_plugin_list()

    def on_plugin_state_changed(self, item):
        plugin_id = item._plugin_id
        state = item.checkState() == QtCore.Qt.Checked
        self._interface.set_plugin_state(plugin_id, state)
        self._rewrite_plugin_config()


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

        self.table_plugin_settings.setRowCount(len(settings))

        for index, (name, handle) in enumerate(settings.items()):
            item_label = QtGui.QTableWidgetItem()
            item_label.setText(handle.label)
            self.table_plugin_settings.setItem(index, 0, item_label)

            item_default = QtGui.QTableWidgetItem()
            item_default.setText(str(handle.default))
            item_default.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table_plugin_settings.setItem(index, 1, item_default)

            setting_widget = self._get_widget_for_setting(name, handle)
            if isinstance(setting_widget, QtGui.QTableWidgetItem):
                self.table_plugin_settings.setItem(index, 2, setting_widget)
            else:
                self.table_plugin_settings.setCellWidget(index, 2, setting_widget)

            item_desc = QtGui.QTableWidgetItem()
            item_desc.setText(handle.description)
            self.table_plugin_settings.setItem(index, 3, item_desc)

    def _do_update_setting(self, setting_id, value):
        self._interface.update_setting(self._current_plugin, setting_id, value)
        self._interface.write_configuration()

        # Check whether the setting is a runtime setting 
        setting_handle = self._current_plugin_instance.get_config().get_setting_handle(setting_id)
        if not setting_handle.is_dynamic():
            self._show_restart_hint()


    def _on_setting_bool_changed(self, setting_id, value):
        self._do_update_setting(setting_id, value == QtCore.Qt.Checked)

    def _on_setting_scalar_changed(self, setting_id, value):
        self._do_update_setting(setting_id, value)

    def _on_setting_enum_changed(self, setting_id, value):
        self._do_update_setting(setting_id, value)

    def _get_widget_for_setting(self, setting_id, setting):
        """ Returns an appropriate widget to control the given setting """

        if setting.type == "BOOL":
            box = QtGui.QCheckBox()
            box.setChecked(QtCore.Qt.Checked if setting.value else QtCore.Qt.Unchecked)
            box.setStyleSheet("margin-left:45%; margin-right:45%;")
            connect(box, QtCore.SIGNAL("stateChanged(int)"), 
                partial(self._on_setting_bool_changed, setting_id))
            return box

        elif setting.type == "INT":
            box = QtGui.QSpinBox()
            box.setMinimum(setting.min_value)
            box.setMaximum(setting.max_value)
            box.setValue(setting.value)
            box.setAlignment(QtCore.Qt.AlignCenter)
            connect(box, QtCore.SIGNAL("valueChanged(int)"), 
                partial(self._on_setting_scalar_changed, setting_id))
            return box

        elif setting.type == "FLOAT":
            box = QtGui.QDoubleSpinBox()
            box.setMinimum(setting.min_value)
            box.setMaximum(setting.max_value)
            box.setValue(setting.value)
            box.setAlignment(QtCore.Qt.AlignCenter)
            connect(box, QtCore.SIGNAL("valueChanged(double)"), 
                partial(self._on_setting_scalar_changed, setting_id))
            return box

        elif setting.type == "ENUM":
            box = QtGui.QComboBox()
            for value in setting.values:
                box.addItem(value)
            connect(box, QtCore.SIGNAL("currentIndexChanged(QString)"), 
                partial(self._on_setting_enum_changed, setting_id))
            box.setCurrentIndex(setting.values.index(setting.value))

            return box

        fallback = QtGui.QTableWidgetItem()
        fallback.setText("??" + setting.type)
        return fallback

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
            item.setText(plugin.get_name())

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

