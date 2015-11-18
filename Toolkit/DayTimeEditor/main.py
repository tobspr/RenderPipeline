
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


from CurveWidget import CurveWidget

class DayTimeEditor(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.resize(1200, 800)

        self.centralwidget = QtGui.QWidget(self)

        widget = CurveWidget(self)
        widget.setGeometry(40, 40, 500, 400)

# Start application
app = QtGui.QApplication(sys.argv)
editor = DayTimeEditor()
editor.show()
app.exec_()
