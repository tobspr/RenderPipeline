

from panda3d.core import PStatCollector


__all__ = ["protected", "profile"]

def protected(func):
    """ Function decorator to mark whether a function is public or protected """
    return func

def profile(func):
    """ Handy decorator which can be used to profile a function with pstats """
    collectorName = "Debug:%s" % func.__name__

    # Insert the collector to a custom dictionary attached to the base
    if hasattr(base, 'custom_collectors'):
        if collectorName in base.custom_collectors.keys():
            pstat = base.custom_collectors[collectorName]
        else:
            base.custom_collectors[collectorName] = PStatCollector(collectorName)
            pstat = base.custom_collectors[collectorName]
    else:
        pstat = PStatCollector(collectorName)
        base.custom_collectors = {}
        base.custom_collectors[collectorName] = pstat

    def doPstat(*args, **kargs):
        pstat.start()
        returned = func(*args, **kargs)
        pstat.stop()
        return returned

    doPstat.__name__ = func.__name__
    doPstat.__dict__ = func.__dict__
    doPstat.__doc__ = func.__doc__
    
    return doPstat