
from PyQt4 import QtGui
from qt.main import Ui_MainWindow as TimeOfDayWindowUI

from CurveWidget import CurveWidget
from DayProperty import *
from DebugObject import DebugObject


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
        self.currentProperty = None
        self.widget = CurveWidget(self.curveBG)
        self.propertyList.selectionModel().selectionChanged.connect(
            self.selectedProperty)
        self.timeOfDay = timeOfDay
        self.fillList()
        self.savePath = None

    def setSavePath(self, pth):
        self.savePath = pth

    def save(self):
        if self.savePath is None:
            self.error("Save path not set! Use setSavePath")
            return

        self.debug("Saving to", self.savePath)
        self.timeOfDay.save(self.savePath)

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

        for propid, prop in self.timeOfDay.getProperties().items():

            if "." in propid:
                # I like cats
                cat = propid.split(".")[0]
                if cat is not currentCat:
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

    def resetProperty(self):
        if self.currentProperty is not None:
            defVal = self.currentProperty.propType.asUniform(
                self.currentProperty.defaultValue) * 999.0

            for slider in self.sliders:
                slider.setValue(defVal)

    def sliderChanged(self):
        """ Gets called when the user moved a slider """
        if self.currentProperty is None:
            return

        for index, slider in enumerate(self.sliders):
            rawVal = slider.value() / 999.0
            adjVal = self.currentProperty.propType.fromUniform(rawVal)
            self.currentProperty.setValue(index, adjVal)

        self.currentProperty.recompute()
        self.curveBG.update()

    def loadProperty(self, prop):
        """ Gets called when another property got selected """
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

    def resetCurve(self):
        for slider in self.sliders:
            slider.setValue(100)
