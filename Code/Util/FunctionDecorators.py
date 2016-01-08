"""

RenderPipeline

Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
 	 	    	 	
"""


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
