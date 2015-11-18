
import math
import sys

import PyQt4.QtCore as QtCore 
import PyQt4.QtGui as QtGui

from panda3d.core import NurbsCurve, Vec3, Notify, HermiteCurve


class Curve:

    """ Interface to the NURBS curve which also manages connecting the end of the
    curve with the beginning """

    def __init__(self):
        self._curve = HermiteCurve()

        # Don't change the order, the NURBS curve interface seems to be buggy
        self._order = 3
        # self._curve.set_order(self._order)
        self._border_points = self._order
        self._cv_points = [
            (0.0, 1),
            (0.25, 0),
            (0.5, 0.4),
            (0.75, 0),
            (1.0, 1)
        ]

        self.build_curve()

    def get_cv_points(self):
        return self._cv_points

    def build_curve(self):

        self._curve.remove_all_cvs()

        curve_type = 4 # HC_SMOOTH, see hermiteCurve.h


        # Duplicate curve at the beginning
        for i in range(self._border_points):
            end_point = self._cv_points[ (-i + self._border_points - 1) % len(self._cv_points) ]
            # end_point = self._cv_points[-1]
            self._curve.append_cv(curve_type, 0.0, end_point[1], 0)
            
        # Append the actual points
        for point in self._cv_points:
            self._curve.append_cv(curve_type, point[0], point[1], 0)

        # Duplicate curve at the end
        for i in range(self._border_points):
            start_point = self._cv_points[i % len(self._cv_points)]
            # start_point = self._cv_points[0]
            self._curve.append_cv(curve_type, 1.0, start_point[1], 0)

        self._curve.recompute()

    def get_value(self, offset): 
        real_points = len(self._cv_points)
        offset_scale = offset * float(real_points - 1)
        offset_scale += self._border_points
        point = Vec3(0)
        self._curve.get_point(offset_scale, point)
        return point.y    

class CurveWidget(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.curves = []

        curve = Curve()
        self.curves.append(curve)

        self._cv_point_size = 3
        self._legend_border = 25

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()


    def mousePressEvent(self, QMouseEvent):
        print QMouseEvent.pos()

    def mouseReleaseEvent(self, QMouseEvent):
        cursor =QtGui.QCursor()
        print cursor.pos()    

    def _get_y_value_for(self, local_value):
        local_value = max(0, min(1.0, 1.0 - local_value))
        local_value *= self.height() - self._legend_border
        return local_value

    def drawWidget(self, painter):

        canvas_width = self.width() - self._legend_border
        canvas_height = self.height() - self._legend_border

        # Draw field background
        pen = QtGui.QPen(QtGui.QColor(25, 25, 25))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(QtGui.QColor(230, 230, 230))
        # painter.drawRect(self._legend_border, 0, self.width() - 1, self.height() - 1 - self._legend_border)

        # Draw legend
        pen.setColor(QtGui.QColor(200, 200, 200))
        painter.setPen(pen)
    
        line_spacing = 20
        num_vert_lines = int(math.ceil(canvas_width / float(line_spacing)))
        num_horiz_lines = int(math.ceil(canvas_height / float(line_spacing)))
        for i in range(num_vert_lines):
            line_pos = i*line_spacing + self._legend_border 
            painter.drawLine(line_pos, 0, line_pos, canvas_height)

        for i in range(num_horiz_lines):
            line_pos = canvas_height - i*line_spacing
            painter.drawLine(self._legend_border, line_pos, self.width(), line_pos)

        # Draw curve
        # painter.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.HighQualityAntialiasing | QtGui.QPainter.SmoothPixmapTransform)
        pen.setColor(QtGui.QColor(0, 0, 0))
        painter.setPen(pen)

        for curve in self.curves:
            last_value = 0
            for i in range(canvas_width):
                rel_offset = i / (canvas_width - 1.0)
                curve_height = self._get_y_value_for(curve.get_value(rel_offset))

                if i == 0:
                    last_value = curve_height

                painter.drawLine(self._legend_border + i-1, last_value, self._legend_border + i, curve_height)
                last_value = curve_height
        
        # painter.setRenderHints(QtGui.QPainter.Antialiasing, on=False)

            # Draw CV points
            pen.setColor(QtGui.QColor(100, 150, 100))
            painter.setPen(pen)
            painter.setBrush(QtGui.QColor(240, 240, 240))

            for x, y in curve.get_cv_points():
                offs_x = x * canvas_width + self._legend_border
                offs_y = (1-y) * canvas_height
                painter.drawRect(offs_x - self._cv_point_size, offs_y - self._cv_point_size, 
                    2*self._cv_point_size, 2*self._cv_point_size)



