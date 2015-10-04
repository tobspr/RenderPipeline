
from panda3d.core import Vec3

from ..Util.DebugObject import DebugObject


class Light(DebugObject):

    """ This is the abstract base class for all Lights """

    # Light Types
    LT_NONE = 0
    LT_POINT_LIGHT = 1

    def __init__(self):
        DebugObject.__init__(self, "Light")
        self._dirty = False
        self._position = Vec3(0)
        self._color = Vec3(0)

    def get_light_type(self):
        """ Returns the type of the light, should be overriden by subclasses """
        raise NotImplementedError()

    def add_to_stream(self, command):
        """ Adds the light to a command stream, subclasses should implement this,
        and call this method, then add their own data """
        command.push_int(self.get_slot())
        command.push_int(self.get_light_type())
        command.push_vec3(self._position)
        command.push_vec3(self._color)

    def set_pos(self, *args):
        """ Sets the light position. Accepts the same parameters as a Vec3 """
        self._position = Vec3(*args)
        self._mark_dirty()

    def set_color(self, *args):
        """ Sets the light color. Accepts the same parameters as a Vec3 """
        self._color = Vec3(*args)
        self._mark_dirty()

    def is_dirty(self):
        """ Returns whether the light needs an update """
        return self._dirty

    def set_slot(self, slot):
        """ Internal method to set a slot """
        self.__slot = slot

    def has_slot(self):
        """ Internal method to check whether a slot is assigned """
        return hasattr(self, "__slot")

    def get_slot(self):
        """ Returns the slot if it is assigned, otherwise it throws an
            exception """
        return self.__slot

    def remove_slot(self):
        """ Removes the slot assigned to the light """
        del self.__slot

    def _mark_dirty(self):
        """ Marks the light as dirty, it will get updated at the beginning of
        the next frame """
        self._dirty = True

    def _unset_dirty(self):
        """ Marks the light as no longer dirty, this should only be called by
        the light manager """

    def __repr__(self):
        """ Returns a representative string of the light """
        return "Light(type={0}, pos={1}, color={2})".format(
            self.get_light_type(), self._position, self._color)
