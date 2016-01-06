

from panda3d.core import PStatCollector
from ..Globals import Globals

__all__ = ["profile"]


def profile(func):
    """ Handy decorator which can be used to profile a function with pstats """
    collector_name = "Debug:%s" % func.__name__

    global_showbase = Globals.base

    # Insert the collector to a custom dictionary attached to the base
    if hasattr(global_showbase, 'custom_collectors'):
        if collector_name in global_showbase.custom_collectors.keys():
            pstat = global_showbase.custom_collectors[collector_name]
        else:
            global_showbase.custom_collectors[collector_name] = \
                PStatCollector(collector_name)
            pstat = global_showbase.custom_collectors[collector_name]
    else:
        pstat = PStatCollector(collector_name)
        global_showbase.custom_collectors = {}
        global_showbase.custom_collectors[collector_name] = pstat

    def do_pstat(*args, **kargs):
        pstat.start()
        returned = func(*args, **kargs)
        pstat.stop()
        return returned

    do_pstat.__name__ = func.__name__
    do_pstat.__dict__ = func.__dict__
    do_pstat.__doc__ = func.__doc__
    return do_pstat
