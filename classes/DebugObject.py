 
# When writing output to file, ensure it exists:
# with open("log.txt", "w") as myfile:
#     pass



# Provides simple functions for debugging
# Most classes inherit from this class
class DebugObject:

    # Inits the object with a given name
    def __init__(self, name):
        self._debug_name = str(name)

    # Debug output, can be disabled later
    def debug(self, *args):
        st = self._debug_name + ": "+  ' '.join([str(i) for i in args])
        self._writeDebugFile(st)
        print st

    # Output some warning, which can be ignored
    def warn(self, *args):
        st = "Warning:" + self._debug_name + ": " + ' '.join([str(i) for i in args])
        self._writeDebugFile(st)
        print st

    # Output some serious error
    def error(self, *args):
        st = "Error:" + self._debug_name + ": " +  ' '.join([str(i) for i in args])
        self._writeDebugFile(st)
        print st

    # Internal method to store log to debug file
    # Currently disabled
    def _writeDebugFile(self, content):
        return
        # with open("log.txt", "a") as myfile:
            # myfile.write(content + "\n")