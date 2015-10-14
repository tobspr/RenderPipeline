
from __future__ import print_function

import sys

# Load and init colorama, used to color the output
from ..External.Colorama import init as init_colorama
from ..External.Colorama import Fore, Style
init_colorama()


class DebugObject:

    """ Provides the functions debug, warn, error and fatal for classes which
    inherit from this object, including the name of the class when printing out
    the message. Most classes inherit from this class. """

    _output_level = 0
    _output_levels = ["debug", "warning", "error", "fatal"]

    @classmethod
    def set_output_level(cls, level):
        """ Sets the output level, messages with a level below will not be
        printed. E.g. if you set the output level to "error", only error and
        fatal messages will be shown.  """
        assert(level in cls._output_levels)
        cls._output_level = cls._output_levels.index(level)

    def __init__(self, name=None):
        """ Initiates the DebugObject with a given name. The name should be
        representative about the class. If no name is given, the classname
        is used """
        if name is None:
            name = self.__class__.__name__
        self._rename(name)
        self._muted = False
        self._debug_color = Fore.GREEN

    def _set_debug_color(self, color, style=None):
        """ Sets the color used to output debug messages """
        self._debug_color = getattr(Fore, color.upper())
        if style:
            self._debug_color+= getattr(Style, style.upper())

    def mute(self):
        """ Mutes this object. This prevents any further output """
        self._muted = True

    def unmute(self):
        """ Unmutes this object. Undoes a mute(), and lets this
        Object instance continue to write debug output """
        self._muted = False

    def get_name(self):
        """ Returns the name of the debug object """
        return self._debug_name

    def debug(self, *args):
        """ Outputs a debug message, something that is not necessarry
        but provides useful information for the developer """
        if self._muted or self._output_level > 0:
            return
        print(self._debug_color + ">> " + \
            self._debug_name.ljust(25) + " " + Style.RESET_ALL + Fore.WHITE +\
            ' '.join([str(i) for i in args]), Fore.RESET + Style.RESET_ALL)

    def warn(self, *args):
        """ Outputs a warning message, something that failed or does
        not work, but does not prevent the program from running """
        if self._muted or self._output_level > 1:
            return
        print(Fore.YELLOW + Style.BRIGHT + "[!] " + (self._debug_name).ljust(25) + \
            Fore.YELLOW + Style.BRIGHT + " " + ' '.join([str(i) for i in args]) + \
            Fore.RESET + Style.RESET_ALL)

    def error(self, *args):
        """ Outputs an error message, something really serious.
        Hopefully this never get's called! Errors also can't be muted """
        if self._output_level > 2:
            return
        print(Fore.RED + Style.BRIGHT + "\n\n\n[!!!] " + \
            (self._debug_name).ljust(23) + " " + ' '.join([str(i) for i in args]) + \
            "\n\n\n" + Fore.RESET + Style.RESET_ALL)

    def fatal(self, *args):
        """ Outputs a fatal error message, printing out the errors and then
        calling sys.exit to terminate the program. This method should be called
        when something failed so hard that the pipeline has to exit. """
        # We have to set output level to 0 here, so we can print out errors
        self._output_level = 0
        self.error(*args)
        sys.exit(0)

    def _rename(self, name):
        """ Renames this object """
        self._debug_name = name

    def __repr__(self):
        """ Represents this object. Subclasses can override this """
        return self._debug_name
