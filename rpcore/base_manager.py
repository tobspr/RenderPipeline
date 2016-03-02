"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

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

from rpcore.rpobject import RPObject

class BaseManager(RPObject):

    """ Base class for all managers, providing utility functions like timing
    the update duration."""

    def __init__(self):
        """ Inits the manager """
        RPObject.__init__(self)
        self._update_collector = PStatCollector(
            "App:Show code:RP_UpdateManagers:" + self.debug_name)

    def update(self):
        """ Updates the manager, this just calls the do_update() method and
        times it """
        self._update_collector.start()
        self.do_update()
        self._update_collector.stop()

    def do_update(self):
        """ Abstract update method, all managers should implement this """
        raise NotImplementedError()
