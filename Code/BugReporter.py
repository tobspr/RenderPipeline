
from DebugObject import DebugObject
from Globals import Globals
from MemoryMonitor import MemoryMonitor

from panda3d.core import OFileStream, ConfigVariableManager, Texture, PNMImage

import datetime
import sys
import os
import struct
import pprint
import time
import shutil

from os.path import join, isdir
from cStringIO import StringIO



# Log stdout and stderr
class Log(object):
    def __init__(self, orig_out):
        self.orig_out = orig_out
        self.log = StringIO()

    def write(self, msg):
        self.orig_out.write(msg)
        self.log.write(msg) 

    def getLog(self):
        return self.log.getvalue() 

sys.stdout = Log(sys.stdout)
sys.stderr = Log(sys.stderr)



class BugReporter(DebugObject):

    """ This class collects all required data from the rendering pipeline and
    creates a bug report which is then merged with the current buffer information
    into a zip file """

    def __init__(self, pipeline):
        DebugObject.__init__(self, "BugReporter")
        self.debug("Creating bug report")


        reportDir = "BugReports/" + str(int(time.time())) + "/"
        reportFname = "BugReports/" + str(int(time.time())) + ""
        if not isdir(reportDir):
            os.makedirs(reportDir)

        # Generate general log
        DebugLog =  "Pipeline Bug-Report\n"
        DebugLog += "Created: " + datetime.datetime.now().isoformat() + "\n"
        DebugLog += "System: " + sys.platform + " / " + os.name + " (" +  str(8 * struct.calcsize("P")) + " Bit)\n"

        with open(join(reportDir, "general.log"), "w") as handle:
            handle.write(DebugLog)

        # Write stdout and stderr
        with open(join(reportDir, "stdout.log"), "w") as handle:
            handle.write(sys.stdout.getLog())

        with open(join(reportDir, "stderr.log"), "w") as handle:
            handle.write(sys.stderr.getLog())

        # Write the scene graph
        handle = OFileStream(join(reportDir, "scene_graph.log")) 
        Globals.render.ls(handle)
        handle.close()

        # Write the pipeline settings
        SettingLog = "# Pipeline Settings Diff File:\n\n"

        for key, val in pipeline.settings.settings.iteritems():
            if val.value != val.default:
                SettingLog += key + " = " + str(val.value) + " (Default " + str(val.default) + ")\n"

        with open(join(reportDir, "pipeline.ini"), "w") as handle:
            handle.write(SettingLog)

        # Write the panda settings
        handle = OFileStream(join(reportDir, "pandacfg.log")) 
        ConfigVariableManager.getGlobalPtr().writePrcVariables(handle)
        handle.close()


        # Write lights and shadow sources
        with open(join(reportDir, "lights.log"), "w") as handle:
            pp = pprint.PrettyPrinter(indent=4, stream=handle)
            handle.write("\nLights:\n")
            pp.pprint(pipeline.lightManager.lightSlots)
            handle.write("\n\nShadowSources:\n")
            pp.pprint(pipeline.lightManager.shadowSourceSlots)

        # Extract buffers
        bufferDir = join(reportDir, "buffers")

        if not isdir(bufferDir):
            os.makedirs(bufferDir)

        for name, (size, entry) in MemoryMonitor.memoryEntries.iteritems():
            if type(entry) == Texture:
                w, h = entry.getXSize(), entry.getYSize()
                # Ignore buffers
                if h < 2:
                    continue                
                pipeline.showbase.graphicsEngine.extractTextureData(entry, pipeline.showbase.win.getGsg())
                
                if not entry.hasRamImage():
                    print "Ignoring", name
                    continue
                pnmSrc = PNMImage(w, h, 4, 2**16-1)
                entry.store(pnmSrc)

                pnmColor = PNMImage(w, h, 3, 2**16-1)
                pnmColor.copySubImage(pnmSrc, 0, 0, 0, 0, w, h)
                pnmColor.write(join(bufferDir, name + "-color.png"))               

                pnmAlpha = PNMImage(w, h, 3, 2**16-1)
                pnmAlpha.copyChannel(pnmSrc, 3, 0)
                pnmAlpha.write(join(bufferDir, name + "-alpha.png"))               

        shutil.make_archive(reportFname, 'zip', reportDir)
        shutil.rmtree(reportDir)
        self.debug("Bug report saved: ", reportFname + ".zip")