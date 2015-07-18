
from PyQt4 import QtGui
from qt.main import Ui_MainWindow as TimeOfDayWindowUI

from CurveWidget import CurveWidget
from DayProperty import *
from DebugObject import DebugObject

from os.path import isdir, isfile, join


class TimeOfDayWindow(QtGui.QMainWindow, TimeOfDayWindowUI, DebugObject):

    def __init__(self, timeOfDay):
        QtGui.QMainWindow.__init__(self)
        DebugObject.__init__(self, "TimeOfDayEditor")
        self.setupUi(self)

        self.sliders = [
            self.slider00,
            self.slider03,
            self.slider06,
            self.slider09,
            self.slider12,
            self.slider15,
            self.slider18,
            self.slider21,
        ]

        for slider in self.sliders:
            slider.valueChanged.connect(self.sliderChanged)

        self.btnReset.clicked.connect(self.resetProperty)
        self.btnSmooth.clicked.connect(self.smoothProperty)
        self.btnSave.clicked.connect(self.save)
        self.btnGenerateClasses.clicked.connect(self.generateClasses)
        self.currentProperty = None
        self.widget = CurveWidget(self.curveBG)
        self.propertyList.selectionModel().selectionChanged.connect(
            self.selectedProperty)
        self.timeOfDay = timeOfDay
        self.fillList()
        self.savePath = None
        self.autoClassPath = None
        self.shaderIncludePath = None

        self.haveUnsavedChanges = False
        self.applicationMovedSlider = False

    def setSavePath(self, pth):
        self.savePath = pth

    def setAutoClassPath(self, pth):
        self.autoClassPath = pth

    def setShaderIncludePath(self, pth):
        self.shaderIncludePath = pth

    def generateClasses(self):
        if self.autoClassPath is None:
            self.error("No auto class path specified! Use setAutoClassPath")
            return

        if self.shaderIncludePath is None:
            self.error("No shader include path specified! Use shaderIncludePath")
            return

        copyFiles = ["DayProperty.py", "TimeOfDay.py"]

        replaces = [
            ("from DebugObject import DebugObject",
             "from ..DebugObject import DebugObject")
        ]

        for f in copyFiles:
            with open(f, "r") as handle:
                content = handle.read()

            for find, replace in replaces:
                content = content.replace(find, replace)

            dest = join(self.autoClassPath, f)

            with open(dest, "w") as writeHandle:
                writeHandle.write(content)

        self.debug("Generated class files! Now generating shader files ..")

        self.timeOfDay.saveGlslInclude(join(self.shaderIncludePath, "TimeOfDay.include"))

        self.debug("Done!")

    def closeEvent(self, event):

        if not self.haveUnsavedChanges:
            event.accept()
            return

        quit_msg = "You still have unsaved changes. Are you sure you want to exit?"
        reply = QtGui.QMessageBox.question(self, 'Confirm',
                                           quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def save(self):
        if self.savePath is None:
            self.error("Save path not set! Use setSavePath")
            return

        self.debug("Saving to", self.savePath)
        self.timeOfDay.save(self.savePath)
        self.haveUnsavedChanges = False

    def selectedProperty(self):
        selected = self.propertyList.selectedItems()[0]
        propertyId = str(selected.toolTip())
        if len(propertyId) < 1:
            # nothing selected, or a header
            return
        prop = self.timeOfDay.getProperty(propertyId)
        self.loadProperty(prop)

    def fillList(self):
        self.propertyList.clear()
        first = None
        currentCat = None
        boldFont = self.font()
        boldFont.setBold(True)

        for propid in self.timeOfDay.getPropertyKeys():

            prop = self.timeOfDay.getProperty(propid)
            if "." in propid:
                # I like cats
                cat = propid.split(".")[0]
                if cat != currentCat:
                    # Get a new cat!
                    currentCat = cat
                    header = QtGui.QListWidgetItem()
                    header.setText(self.timeOfDay.categories[cat])
                    header.setToolTip("")
                    header.setFont(boldFont)
                    self.propertyList.addItem(header)

            padding = "" if currentCat is None else "    "

            item = QtGui.QListWidgetItem()
            item.setText(padding + prop.name)
            item.setToolTip(propid)
            self.propertyList.addItem(item)
            if first is None:
                first = item

        self.propertyList.setCurrentItem(first)

    def smoothProperty(self):

        if self.currentProperty is None:
            return

        # save old values
        oldValues = self.currentProperty.values
        oldValues = [oldValues[0]] + oldValues + [oldValues[1]]

        smoothFactor = 0.05

        for i in xrange(8):
            val = oldValues[i + 1]
            valBefore = oldValues[i]
            valAfter = oldValues[i + 2]
            avgBeforeAfter = (valBefore + valAfter) / 2.0
            newVal = avgBeforeAfter * smoothFactor + val * (1.0 - smoothFactor)
            self.currentProperty.setValue(i, newVal)
            asUniform = self.currentProperty.propType.asUniform(newVal) * 999.0
            self.sliders[i].setValue(asUniform)

        self.haveUnsavedChanges = True

    def resetProperty(self):
        if self.currentProperty is not None:
            reply = QtGui.QMessageBox.question(self, 'Confirm',
                                               "Are you sure you want to reset the curve? You can't revert this!", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.Yes:
                defVal = self.currentProperty.propType.asUniform(
                    self.currentProperty.defaultValue) * 999.0

                for slider in self.sliders:
                    slider.setValue(defVal)

            self.haveUnsavedChanges = True

    def sliderChanged(self):
        """ Gets called when the user moved a slider """
        if self.currentProperty is None:
            return

        if not self.applicationMovedSlider:
            self.haveUnsavedChanges = True

        for index, slider in enumerate(self.sliders):
            rawVal = slider.value() / 999.0
            adjVal = self.currentProperty.propType.fromUniform(rawVal)
            self.currentProperty.setValue(index, adjVal)

        self.currentProperty.recompute()
        self.curveBG.update()

    def loadProperty(self, prop):
        """ Gets called when another property got selected """

        self.applicationMovedSlider = True
        self.labelDescription.setText(
            "<strong>" + prop.name + "</strong><br>Description: " + prop.description)

        self.currentProperty = None

        self.lblMaxVal.setText(str(prop.propType.maxVal))
        self.lblMinVal.setText(str(prop.propType.minVal))
        self.lblMidVal.setText(
            str((prop.propType.maxVal + prop.propType.minVal) / 2))

        for index, value in enumerate(prop.values):
            slider = self.sliders[index]
            val = prop.values[index]
            valScaled = prop.propType.asUniform(val)
            slider.setValue(valScaled * 999.0)

        self.currentProperty = prop
        self.widget.setProperty(self.currentProperty)
        self.sliderChanged()

        self.applicationMovedSlider = False
