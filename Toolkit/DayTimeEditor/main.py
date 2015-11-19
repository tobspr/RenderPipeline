
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

connect = QtCore.QObject.connect


class DayTimeEditor(QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)

        self.settings_tree.setColumnWidth(0, 200)
        self.settings_tree.expandAll()

        self.edit_widget = CurveWidget(self)
        self.prefab_edit_widget.addWidget(self.edit_widget)

        connect(self.time_slider, QtCore.SIGNAL("valueChanged(int)"), self._on_time_changed)

        self._on_time_changed(self.time_slider.value())

    def _on_time_changed(self, val):
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
