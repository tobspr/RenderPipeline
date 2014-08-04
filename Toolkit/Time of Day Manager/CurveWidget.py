

from PyQt4 import QtGui
from panda3d.core import NurbsCurve, Vec3


class CurveWidget(QtGui.QWidget):

    """ Simple widget to draw a curve """

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.pen = QtGui.QPen(QtGui.QColor(51, 152, 255))
        self.resize(441, 151)
        self.pen.setWidth(3)
        self.values = [0 for i in xrange(8)]
        self.path = QtGui.QPainterPath()
        self.marginBottom = 14
        self.marginTop = 10
        self.adjustedHeight = 151 - (self.marginBottom + self.marginTop)
        self.curve = NurbsCurve()
        self.curve.setOrder(3)
        self.padAmount = 5
        self.recomputeCurve()
        self.property = None

    def setProperty(self, prop):
        self.property = prop

        for i in xrange(8):
            self.values[i] = self.property.propType.asUniform(
                self.property.values[i])

        self.recomputeCurve()

    def recomputeCurve(self):
        self.curve.removeAllCvs()

        paddedValues = self.values + [self.values[0]]
        for i in xrange(self.padAmount):
            paddedValues = [paddedValues[0]] + \
                paddedValues + [paddedValues[-1]]

        for index, val in enumerate(paddedValues):
            self.curve.appendCv(Vec3(index / 8.0, val, 0.0))
        self.curve.recompute()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(self.pen)

        maxT = self.curve.getMaxT() - 2.0 * (self.padAmount - 1)
        # maxT = self.curve.getMaxT()
        offset = self.padAmount - 1
        pt = Vec3(0)

        for i in xrange(441):
            self.curve.getPoint((i / 441.0) * maxT + offset,  pt)
            painter.drawPoint(
                i, 151 - (pt.y * self.adjustedHeight) - self.marginBottom)
