
"""

This tool offers an interface to configure the pipeline

"""

from __future__ import print_function
import sys


# Load the generated UI Layout
from ui.main_window_generated import Ui_MainWindow


# Load all PyQt classes
try:
    import PyQt4.QtCore as QtCore 
    import PyQt4.QtGui as QtGui
except ImportError as msg:
    print("Failed to import PyQt4:", msg)
    print("Please make sure you installed PyQt!")
    sys.exit(1)


class PluginConfigurator(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)


# Start application
app = QtGui.QApplication(sys.argv)
configurator = PluginConfigurator()
configurator.show()


app.exec_()

