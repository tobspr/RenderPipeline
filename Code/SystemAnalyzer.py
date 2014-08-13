
import sys
import os
import struct
import datetime

from panda3d.core import PandaSystem


class SystemAnalyzer():

    """ Small tool to analyze the system and also check if the users panda
    build is out of date """

    @classmethod
    def analyze(self):
        """ Analyzes the user system. This should help debugging when the user
        shares his log """
        print "System analyzer:"

        def stat(name, *args):
            print " ", str(name).ljust(20, " "), "=", ''.join([str(i) for i in args])

        stat("System", sys.platform, " / ", os.name)
        stat("Bitness", 8 * struct.calcsize("P"))
        stat("Panda3D-Build Date", PandaSystem.getBuildDate())
        stat("Panda3D-Compiler", PandaSystem.getCompiler())
        stat("Panda3D-Distributor", PandaSystem.getDistributor())
        stat("Panda3D-Version", PandaSystem.getVersionString())
        stat("Panda3D-Platform", PandaSystem.getPlatform())
        stat("Panda3D-Official?", PandaSystem.isOfficialVersion())

    @classmethod
    def checkPandaVersionOutOfDate(self, minDay, minMonth, minYear):
        """ Checks if the panda build is out of date. So users don't complain
        about stuff not working, because they simply didn't update """

        built = PandaSystem.getBuildDate()
        formated = datetime.datetime.strptime(built, "%b %d %Y %H:%M:%S")
        required = datetime.datetime(minYear, minMonth, minDay, 12, 00)

        if formated < required:
            print "ERROR: Your Panda3D Build is out of date. Update to the latest"
            print "CVS build in order to use the pipeline!"
            sys.exit(0)

        # Check version
        versionMinMinor = 9
        versionMinMajor = 1

        versionMismatch = False
        if PandaSystem.getMajorVersion() < versionMinMajor:
            versionMismatch = True
        elif PandaSystem.getMinorVersion() < versionMinMinor:
            versionMismatch = True

        if versionMismatch:
            print "ERROR: Your current panda build (", PandaSystem.getVersionString(), ") is"
            print "not supported! The minimum required build is", str(versionMinMajor) + "." + str(versionMinMinor) + ".0"
            sys.exit(0)

if __name__ == "__main__":
    SystemAnalyzer.analyze()
    SystemAnalyzer.checkPandaVersionOutOfDate(7,8,2014)
