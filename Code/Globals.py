
class Globals(object):

    """ This class is a singleton to store globals because cython can't handle
    global variables. """

    base = None
    loader = None
    render = None
    clock = None
    font = None
    resolution = None

    def __init__(self):
        raise NotImplementedError("Class is a singleton")

    @classmethod
    def load(cls, showbase):
        """ Fetches the globals from a given showbase """
        cls.base = showbase
        cls.loader = showbase.loader
        cls.render = showbase.render
        cls.clock = showbase.taskMgr.globalClock
        cls.font = None
        cls.resolution = None
