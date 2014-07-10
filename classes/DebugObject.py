
from ConsoleColors import printRedConsoleText, printYellowConsoleText

class DebugObject:

    """ Provides the functions debug, warn, error for classes
    which inherit from this object, including the name of the
    class when printing out the message. Most classes inherit
    from this class. """

    def __init__(self, name):
        """ Initiates the DebugObject with a given name. The
        name should equal to the classname, or at least
        representative """
        self._debug_name = str(name)
        self.muted = False

    def mute(self):
        """ Mutes this object. This prevents any further output """
        self.muted = True

    def unmute(self):
        """ Unmutes this object. Undoes a mute(), and lets this
        Object instance continue to write debug output """
        self.muted = False

    def debug(self, *args):
        """ Outputs a debug message, something that is not necessarry
        but provides useful information for the developer """
        if self.muted:
            return
        print self._debug_name + ": " + ' '.join([str(i) for i in args])

    def warn(self, *args):
        """ Outputs a warning message, something that failed or does
        not work, but does not prevent the program from running """
        if self.muted:
            return
        printYellowConsoleText("Warning: " + self._debug_name +
            ": " + ' '.join([str(i) for i in args]) + "\n")

    def error(self, *args):
        """ Outputs an error message, something really serious.
        Hopefully this never get's called! Errors also can't be muted """
        printRedConsoleText("Error: " + self._debug_name + ": " + \
            ' '.join([str(i) for i in args])+ "\n")

    def __repr__(self):
        """ Represents this object. Subclasses should properly implement
        this """
        return self._debug_name + "[]"
