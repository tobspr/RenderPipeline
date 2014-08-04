import sys
import math
from PyQt4 import QtGui

from TimeOfDayManager import TimeOfDayManager
from TimeOfDay import TimeOfDay

from os.path import isdir, isfile, join


if __name__ == "__main__":
    print "Starting TimeOfDay Editor"
    app = QtGui.QApplication(sys.argv)

    rootDir = "../../"
    configDir = rootDir + "Config/"
    configFile = join(configDir, "time_of_day.ini")
    timeOfDay = TimeOfDay()

    if not isfile(configFile):
        print "Creating default config file"
        timeOfDay.writeDefaultFile(configFile)    

    timeOfDay.load(configFile)

    manager = TimeOfDayManager()
    sys.exit(app.exec_())