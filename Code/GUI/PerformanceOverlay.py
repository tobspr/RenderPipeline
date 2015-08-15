
from ..Globals import Globals
from ..DebugObject import DebugObject
from FastText import FastText

from direct.gui.DirectFrame import DirectFrame
from panda3d.core import PStatClient, Vec2, Vec3


import os
import subprocess
import atexit
import time

class PerformanceOverlay(DebugObject):


    def __init__(self, pipeline):
        DebugObject.__init__(self, "PerformanceOverlay")
        self.pipeline = pipeline
        self.debug("Init performance overlay ..")
        self.visible = False
        self.frameIndex = 0
        self.numSamples = 0
        self.avgSamples = 60
        self.lastTextUpdate = 0
        self.frameDataRdy = False
        self.setup()
        self.hide()

    def setup(self):

        self.tryStartPstats()

        self.averagedEntries = []


        self.node = Globals.base.aspect2d.attachNewNode("PerfOverlay")

        ww, wh = Globals.base.win.getXSize(), Globals.base.win.getYSize()



        bg = DirectFrame(parent=self.node,
                       frameColor=(0.1, 0.1, 0.1, 0.9),
                       frameSize=(-1.45, 1.45, -0.78, 0.67))  # state=DGG.NORMAL

        self.textLines = []
        self.averages = {}

        for col in xrange(3):
            for i in xrange(25):
                yoffs = 0.6 - i * 0.055
                xoffs = -0.95 + col * 0.95
                bgcol = (0, 0, 0, 0.2) if i % 2 == 0 else (0.3, 0.3, 0.3, 0.1)


                if i == 0:
                    bgcol = (0.34, 0.56, 0.2, 1)

                bgRow = DirectFrame(parent=self.node, frameColor=bgcol, pos=(xoffs, 0, yoffs), 
                            frameSize=(-0.46, 0.46, -0.027, 0.028))

                txtLeft = FastText(pos=Vec2(-0.4+xoffs, yoffs), rightAligned=False, color=Vec3(1, 1, 1), size=0.03, parent=self.node)
                txtLeft.setText("This is demo line " + str(i))

                txtRight = FastText(pos=Vec2(0.4 + xoffs, yoffs), rightAligned=True, color=Vec3(1, 1, 1), size=0.03, parent=self.node)
                txtRight.setText("32.000")

                if i > 0:
                    self.textLines.append((txtLeft, txtRight))
                else:
                    txtLeft.setText("Name")
                    txtLeft.setColor(1,1,0)
                    txtRight.setText("Time [ms]")
                    txtRight.setColor(1,1,0)


    def tryStartPstats(self):
        """ Starts the 'text-stats' PStatClient and connects to that client, in order
        to make pstats generate timings """
        self.procHandle = None

        if not PStatClient.getGlobalPstats().isConnected():
            self.debug("Starting dummy pstats (text-stats)")
            nullFile = open(os.devnull, 'w')
            self.procHandle = subprocess.Popen(["text-stats"], stdout=nullFile, stderr=nullFile)
            atexit.register(self.stopPstats)
            PStatClient.connect()
        else:
            self.debug("PStats already running")

    def stopPstats(self):
        self.debug("Stopping dummy pstats")
        try:
            self.procHandle.kill()
        except Exception, msg:
            self.debug("Couldn't stop dummy pstats!")


    def update(self):

        if not self.visible:
            return

        self.frameIndex += 1

        self.updateTimings()

        tdiff = time.time() - self.lastTextUpdate

        # Don't update the texts every frame
        if tdiff > 0.3:
            self.lastTextUpdate = time.time()

            for textLeft, textRight in self.textLines:
                textLeft.hide()
                textRight.hide()

            for idx, (name, dur) in enumerate(self.averagedEntries):
                if idx >= len(self.textLines):
                    break
                self.textLines[idx][0].setText(name.replace("~", "").replace("Draw:", ""))  
                self.textLines[idx][1].setText("{:5.2f}".format(dur * 1000.0))  
                self.textLines[idx][0].show()
                self.textLines[idx][1].show()

                if name.startswith("~"):
                    self.textLines[idx][0].setColor(1, 1, 0)
                    self.textLines[idx][1].setColor(1, 1, 0)
                else:
                    self.textLines[idx][0].setColor(1, 1, 1)
                    self.textLines[idx][1].setColor(1, 1, 1)


    def updateTimings(self):


        client = PStatClient.getGlobalPstats()
        gpuData = Globals.base.win.getGsg().getPstatsGpuData()
        numEvents = gpuData.getNumEvents()
        # gpuData.sortTime()

        if numEvents < 1:
            # Somehow pstats didn't start, nothing we can do about that
            self.numSamples = 0
            self.averagedEntries = [("~Please start & connect to pstats!", 0)]
            return

        dataset = {}
        lastStarts = {}


        for eventIdx in xrange(gpuData.getNumEvents()):
            collectorIdx = gpuData.getTimeCollector(eventIdx)
            collector = client.getCollector(collectorIdx)
            fname = collector.getFullname()

            if fname.count(":") >= 2:
                eventTime = gpuData.getTime(eventIdx)
                isStart = gpuData.isStart(eventIdx)
                
                if isStart:
                    lastStarts[fname] = eventTime
                else:
                    if fname not in lastStarts or lastStarts[fname] < 0:
                        print "ERROR: Overlapping time"

                    start = lastStarts[fname]
                    dur = eventTime - start
                    if fname in dataset:
                        dataset[fname] += dur
                    else:
                        dataset[fname] = dur

                    lastStarts[fname] = -1

        entries = []
        for key, val in dataset.iteritems():
            entries.append((key, val))

        # Create sum
        ftime = 0.0
        for key, dur in entries:
            ftime += dur

        entries.append(("~Total GPU Time", ftime))

        # Compute averages
        for name, dur in entries:
            if name in self.averages:
                self.averages[name] = self.averages[name][1:] + [dur]
            else:
                self.averages[name] = [0.0] * self.avgSamples
        # Generate list 
        self.averagedEntries = []

        for key, val in self.averages.iteritems():
            avg = sum(val) / float(self.avgSamples)
            self.averagedEntries.append((key, avg))

        self.averagedEntries.sort(key=lambda x: -x[1])

        # if self.numSamples < self.avgSamples:
            # self.averagedEntries = [("Collecting Samples ({:3d} / {:3d})".format(self.numSamples, self.avgSamples), 0)]

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()

    def show(self):
        self.numSamples = 0
        self.visible = True
        self.node.show()

    def hide(self):
        self.numSamples = 0
        self.visible = False
        self.node.hide()