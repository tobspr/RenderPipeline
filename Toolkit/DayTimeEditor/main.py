
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

        # self._on_time_changed(self.time_slider.value())


    def setupUi(self):
        """ Setups the UI Components """
        Ui_MainWindow.setupUi(self, self)
        self.settings_tree.setColumnWidth(0, 200)
        self.settings_tree.expandAll()

        self.edit_widget = CurveWidget(self)
        self.prefab_edit_widget.addWidget(self.edit_widget)

        connect(self.time_slider, QtCore.SIGNAL("valueChanged(int)"), self._on_time_changed)

    def _on_time_changed(self, val):
        """ Handler when the time slider got moved """
        hour = val / (60 * 60 * 60)
        minute = (val / (60 * 60)) % 60
        ftime = float(val) / (24 * 60 * 60 * 60)

        self.time_label.setText(str(hour).zfill(2) + ":" + str(minute).zfill(2))
        self.edit_widget.set_current_time(ftime)


# Start application
app = QtGui.QApplication(sys.argv)
editor = DayTimeEditor()
editor.show()
app.exec_()
