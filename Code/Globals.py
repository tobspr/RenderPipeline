


class Globals:

    """ This class is a singleton to store globals because cython can't handle
    global variables. """

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
        self.font = None