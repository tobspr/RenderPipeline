
from six.moves import range

from random import random
from panda3d.core import Vec3, CurveFitter

class SmoothConnectedCurve(object):

    """ Interface to a curve which also manages connecting the end of the
    curve with the beginning. """

    def __init__(self):
        self._curve = None
        self._modified = False

        # Append some points to the border, to make sure the curve matches at
        # the edges
        self._border_points = 1

        # Curve color, used for displaying the curve
        self._color = (0, 0, 0)

        # Control points, those are some demo values
        self._cv_points = [
            [0.1, 0.5 + 0.4 * random()],
            [0.3, 0.2 + 0.2 * random()],
            [0.5, 0.4 + 0.3 * random()],
            [0.75, 0 + 0.3 * random()]
        ]

        # Build the curve
        self.build_curve()

    def was_modified(self):
        """ Returns whether the curve was modified since the creation """
        return self._modified

    def get_cv_points(self):
        """ Returns a list of all controll points """
        return self._cv_points

    def set_color(self, r, g, b):
        """ Sets the display color of the curve """
        self._color = (r, g, b)

    def get_color(self):
        """ Returns the display color of the curve """
        return self._color

    def set_single_value(self, val):
        """ Sets the curve to be linear, and only use a single value """
        self._cv_points = [
            [0.5, val],
        ]
        self._modified = False
        self.build_curve()

    def append_cv(self, x, y):
        """ Appends a new cv and returns the index of the attached cv """
        self._cv_points.append([x, y])
        self.build_curve()
        self._modified = True
        return len(self._cv_points) - 1

    def remove_cv(self, index):
        """ Attempts to remove the cv at the given index, does nothing if only
        one control point is left """
        if len(self._cv_points) > 1:
            del self._cv_points[index]
        self._modified = True
        self.build_curve()

    def build_curve(self):
        """ Rebuilds the curve based on the controll point values """

        sorted_points = sorted(self._cv_points, key=lambda v: v[0])
        first_point = sorted_points[0]
        fitter = CurveFitter()

        # Duplicate curve at the beginning
        for i in range(self._border_points):
            end_point = self._cv_points[(-i + self._border_points - 1) % len(self._cv_points)]
            end_point = first_point
            fitter.add_xyz(0.0, Vec3(0, end_point[1], 0))

        # Append the actual points
        for point in self._cv_points:
            # Clamp point x position to avoid artifacts at the beginning
            point_t = max(0.01, point[0])
            fitter.add_xyz(point_t, Vec3(point_t, point[1], 0))

        # Duplicate curve at the end
        for i in range(self._border_points):
            start_point = self._cv_points[i % len(self._cv_points)]
            start_point = first_point
            fitter.add_xyz(1.0, Vec3(1, start_point[1], 0))

        fitter.sort_points()
        fitter.compute_tangents(1.0)
        self._curve = fitter.make_hermite()

    def set_cv_value(self, index, x_value, y_value):
        """ Updates the cv point at the given index """
        self._cv_points[index] = [x_value, y_value]
        self._modified = True

    def set_cv_points(self, points):
        """ Sets the cv points to the given list of points """
        self._cv_points = points
        self._modified = True
        self.build_curve()

    def get_value(self, offset):
        """ Returns the value on the curve ranging whereas the offset should be
        from 0 to 1 (0 denotes the start of the curve). The returned value will
        be a value from 0 to 1 as well. """
        point = Vec3(0)
        self._curve.evaluate_xyz(offset, point)
        return point.y

    def serialize(self):
        """ Returns the value of the curve as yaml list """
        points = ["[{},{}]".format(round(a, 5), round(b, 5)) for a, b in self._cv_points]
        return "[" + ','.join(points) + "]"
