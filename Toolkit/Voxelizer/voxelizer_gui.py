
import sys
from direct.stdpy.file import isfile, join
from PyQt4 import QtGui
from panda3d.core import Filename
from qt.main import Ui_Voxel
from voxelize import VoxelizerShowbase
from os import system
from thread import start_new_thread


class VoxelizerGUI(QtGui.QMainWindow, Ui_Voxel):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)
        self._log = ""
        self.showbase = VoxelizerShowbase()
        self.clearLog()
        self.lastResultData = None

        self.btn_selectSource.clicked.connect(self.selectSource)
        self.btn_convert.clicked.connect(self.startConvert)
        self.btn_showResult.clicked.connect(self.showResult)

    def showResult(self):
        start_new_thread(self.startViewer, ())

    def startViewer(self):
        system('ppython show_voxels.py "' +
               str(self.lastResultData[0]) + '" "' + str(self.lastResultData[1]) + '"')

    def startConvert(self):

        filename = str(self.ipt_source.text())
        self.btn_showResult.setEnabled(False)

        if len(filename) < 1 or not isfile(filename):
            QtGui.QMessageBox.warning(
                self, "Voxelizer", "You have to select a valid source file first!")
            return

        parentDir = "/".join(filename.split("/")[:-1])
        destination = join(parentDir, "voxelized")
        print "ParentDir:", parentDir

        voxelGridSize = 32
        if self.chb_gridSize16.isChecked():
            voxelGridSize = 16
        elif self.chb_gridSize32.isChecked():
            voxelGridSize = 32
        elif self.chb_gridSize64.isChecked():
            voxelGridSize = 64
        elif self.chb_gridSize128.isChecked():
            voxelGridSize = 128
        elif self.chb_gridSize256.isChecked():
            voxelGridSize = 256
        elif self.chb_gridSize512.isChecked():
            voxelGridSize = 512

        borderSize = float(self.box_borderSize.value())
        self.clearLog()
        self.addLog("Starting to convert ..")
        self.processStatus.setValue(0)

        result = False

        if True:
        # try:
            result = self.showbase.voxelize(filename, parentDir, destination, {
                "gridResolution": voxelGridSize,
                "border": borderSize,
            }, logCallback=self._progressCallback)
        # except Exception, msg:
        if False:
            self.addLog("Fatal error during conversion process!")
            self.addLog("Message: " + str(msg))

        self.processStatus.setValue(0)

        if not result:
            self.addLog("Error: Voxelizer returned non-success statuscode!")
        else:
            self.btn_showResult.setEnabled(True)
            self.lastResultData = (filename, destination)

    def _progressCallback(self, percent, message, isError=False):
        self.addLog("[" + str(int(percent)).rjust(3, ' ') + "%] " + message)
        self.processStatus.setValue(int(percent))

    def selectSource(self):
        print "Select source!"
        self.btn_showResult.setEnabled(False)
        filename = QtGui.QFileDialog.getOpenFileName(self,
                                                     'Select source file ', 'convert/', "P3D Scene File (*.egg *.bam *.pz)")
        filename = str(filename)
        if len(filename) < 1:
            # nothing selected
            pass
        else:
            self.ipt_source.setText(
                Filename.fromOsSpecific(filename).getFullpath())

    def clearLog(self):
        self._log = ""
        self.renderLog()

    def addLog(self, line):
        self._log += line + "\n"
        self.renderLog()

    def renderLog(self):
        self.logOutput.setPlainText(self._log)
        self.logOutput.moveCursor(QtGui.QTextCursor.End)


if __name__ == "__main__":
    print "Starting Voxelizer GUI"

    app = QtGui.QApplication(sys.argv)

    win = VoxelizerGUI()
    win.show()

    sys.exit(app.exec_())
