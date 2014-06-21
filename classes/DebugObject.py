 
class DebugObject:

    def __init__(self, name):
        self._debug_name = str(name)

    def debug(self, *args):
        print self._debug_name + ":", ' '.join([str(i) for i in args])

    def warn(self, *args):
        print "Warning:";self._debug_name + ":", ' '.join([str(i) for i in args])
        
    def error(self, *args):
        print "Error:";self._debug_name + ":", ' '.join([str(i) for i in args])
        