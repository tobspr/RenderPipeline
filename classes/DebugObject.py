 
with open("log.txt", "w") as myfile:
    pass

class DebugObject:

    def __init__(self, name):
        self._debug_name = str(name)

    def debug(self, *args):
        st = self._debug_name + ": "+  ' '.join([str(i) for i in args])
        self._writeDebugFile(st)
        print st

    def warn(self, *args):
        st = "Warning:" + self._debug_name + ": " + ' '.join([str(i) for i in args])
        self._writeDebugFile(st)
        print st

    def error(self, *args):
        st = "Error:" + self._debug_name + ": " +  ' '.join([str(i) for i in args])
        self._writeDebugFile(st)
        print st

    def _writeDebugFile(self, content):
        return
        # with open("log.txt", "a") as myfile:
            # myfile.write(content + "\n")