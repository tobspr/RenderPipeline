


class Globals:

    """ This class stores globals, as cython can't handle
    builtins """

    base = None
    loader = None
    render = None
    clock = None
    
    @classmethod
    def load(self, showbase):
        """ Fetches the globals from a given showbase """
        self.base = showbase
        self.loader = showbase.loader
        self.render = showbase.render
        self.clock = showbase.taskMgr.globalClock
    