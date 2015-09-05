
import sys

# Load and init colorama
from ..External.Colorama import init as init_colorama
from ..External.Colorama import Fore, Back, Style
init_colorama()

from FunctionDecorators import protected

class DebugObject:

    """ Provides the functions debug, warn, error and fatal for classes which 
    inherit from this object, including the name of the class when printing out
    the message. Most classes inherit from this class. """

    _outputLevel = 0
    _outputLevels = ["debug", "warning", "error", "fatal"]

    @classmethod
    def setOutputLevel(self, level):
        """ Sets the output level, messages with a level below will not be printed """
        assert(level in self._outputLevels)
        self._outputLevel = self._outputLevels.index(level)

    def __init__(self, name):
        """ Initiates the DebugObject with a given name. The
        name should equal to the classname, or at least
        representative """
        self._rename(name)
        self.muted = False

    def mute(self):
        """ Mutes this object. This prevents any further output """
        self.muted = True

    def unmute(self):
        """ Unmutes this object. Undoes a mute(), and lets this
        Object instance continue to write debug output """
        self.muted = False

    def getName(self):
        """ Returns the name of the debug object """
        return self._debug_name

    def debug(self, *args):
        """ Outputs a debug message, something that is not necessarry
        but provides useful information for the developer """
        if self.muted or self._outputLevel > 0:
            return
    
        print Fore.GREEN + "[-] " + self._debug_name.ljust(25) + Fore.WHITE +  \
            ' '.join([str(i) for i in args]), Fore.RESET + Style.RESET_ALL

    def warn(self, *args):
        """ Outputs a warning message, something that failed or does
        not work, but does not prevent the program from running """
        if self.muted or self._outputLevel > 1:
            return
        print Fore.YELLOW + Style.BRIGHT + "[!] " + (self._debug_name).ljust(25) + \
            Fore.YELLOW + Style.BRIGHT + ' '.join([str(i) for i in args]) + Fore.RESET + Style.RESET_ALL

    def error(self, *args):
        """ Outputs an error message, something really serious.
        Hopefully this never get's called! Errors also can't be muted """
        if self._outputLevel > 2:
            return
        print Fore.RED + Style.BRIGHT + "\n\n\n[!!!] " + (self._debug_name).ljust(23) + \
            ' '.join([str(i) for i in args])+ "\n\n\n" + Fore.RESET + Style.RESET_ALL

    def fatal(self, *args):
        """ Outputs a fatal error message, printing out the errors and then calling
        sys.exit to terminate the program """
        
        # We have to set output level to 0 here, so we can print out errors
        self._outputLevel = 0
        self.error(*args)
        self.error("Program terminated!")
        sys.exit(0)

    @protected
    def _rename(self, name):
        """ Renames this object """
        self._debug_name = name

    def __repr__(self):
        """ Represents this object. Subclasses can override this """
        return self._debug_name
