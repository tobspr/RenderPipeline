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

import collections

from .DebugObject import DebugObject

class RepeatedTaskQueue(DebugObject):

    """ This class manages a set of tasks. Each time .get_next_task() is called,
    the next task in the queue is returned. When no task is left, the queue
    starts from the beginning again """

    def __init__(self):
        """ Constructs a new empty task queue """
        DebugObject.__init__(self)
        self._tasks = collections.deque()

    def add(self, *args):
        """ Adds a new task to the task queue. task can either be an object,
        or a list of objects """
        self._tasks.extend(args)

    def get_next_task(self):
        """ Returns the next task in the queue """
        task = self._tasks[0]
        self._tasks.rotate(-1)
        return task

    def exec_next_task(self):
        """ Takes the next task in the queue and executes it. This expects the
        task object to be a valid callable, either function or lambda """
        self.get_next_task()()
