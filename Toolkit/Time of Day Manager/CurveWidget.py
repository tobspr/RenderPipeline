
from PyQt4 import QtGui
from panda3d.core import NurbsCurve, Vec3


class CurveWidget(QtGui.QWidget):

    """ Simple widget to draw a curve in qt """

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.pen = QtGui.QPen(QtGui.QColor(51, 152, 255))
        self.resize(441, 151)
        self.pen.setWidth(3)
        self.marginBottom = 12
        self.marginTop = 12
        self.adjustedHeight = 151 - (self.marginBottom + self.marginTop)
        self.prop = None

    def setProperty(self, prop):
        """ Sets the current property to display the curve """
        self.prop = prop

    def paintEvent(self, event):
        """ Draws this curve, gets called by qt """
        painter = QtGui.QPainter(self)
        painter.setPen(self.pen)

        if self.prop is None:
            return

        for i in xrange(441):
            sampled = self.prop.getInterpolatedValue(i / 441.0)
            linear = self.prop.propType.asUniform(sampled)
            painter.drawPoint(
                i, 151 - (linear * self.adjustedHeight) - self.marginBottom)
