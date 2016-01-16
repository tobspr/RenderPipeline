
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
