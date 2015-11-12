
"""

This tool offers an interface to configure the pipeline

"""

from __future__ import print_function
import sys

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

        # self.lst_plugins.connect("onSelectionChanged()", self.on_plugin_selected)
        # self.lst_plugins.selectionChanged.connect(self.on_plugin_selected)
        # QtCore.QObject.connect(self.lst_plugins, QtCore.SIGNAL('selectionChanged()'), self.on_plugin_selected)

        # print(type(self.lst_plugins).selectionChanged)

        connect(self.lst_plugins, QtCore.SIGNAL("itemSelectionChanged()"), self.on_plugin_selected)

        self._load_plugin_list()

    def on_plugin_selected(self):
        """ Gets called when a plugin got selected in the plugin list """
        selected_item = self.lst_plugins.selectedItems()
        assert(len(selected_item) == 1)
        selected_item = selected_item[0]
        self._current_plugin = selected_item._plugin_id
        self._current_plugin_instance = self._interface.get_plugin_by_id(self._current_plugin)
        assert(self._current_plugin_instance is not None)

        self._render_current_plugin()

    def _render_current_plugin(self):
        """ Displays the currently selected plugin """        
        self.lbl_plugin_name.setText(self._current_plugin_instance.get_name())

        version_str = "Version " + self._current_plugin_instance.get_config().get_version()
        version_str += " by " + self._current_plugin_instance.get_config().get_author()

        self.lbl_plugin_version.setText(version_str)
        self.lbl_plugin_desc.setText(self._current_plugin_instance.get_config().get_description())

    def _load_plugin_list(self):
        """ Reloads the whole plugin list """
        print("Loading plugin list")

        # Plugins are all plugins in the plugins directory
        self._interface.unload_plugins()
        self._interface.load_plugins()
        plugins = self._interface.get_plugin_instances()

        self.lst_plugins.clear()

        for plugin in plugins:
            item = QtGui.QListWidgetItem()
            item.setText(plugin.get_name())
            item._plugin_id = plugin.get_id()
            self.lst_plugins.addItem(item)
        


# Start application
app = QtGui.QApplication(sys.argv)
configurator = PluginConfigurator()
configurator.show()


app.exec_()

