
from DebugObject import DebugObject

class DistributedTaskManager(DebugObject):

    """ This tasks handles the chain of multiple tasks, split over several
    frames. Each tasks gets executed for a fixed number of frames, in the order
    they were added """

    def __init__(self):
        DebugObject.__init__(self, "DistributedTaskManager")
        self.tasks = []
        self.frameIndex = 0

    def addTask(self, frameDuration, handle):
        self.tasks.append((frameDuration, handle))

    def clearTasks(self):
        self.tasks = []

    def resetFrameIndex(self):
        self.frameIndex = 0

    def process(self):
        framesRequired = 0
        for numFrames, taskHandle in self.tasks:
            if self.frameIndex >= framesRequired and self.frameIndex < framesRequired + numFrames:
                taskHandle(self.frameIndex - framesRequired)
            framesRequired += numFrames
        self.frameIndex = (self.frameIndex + 1) % framesRequired
