import sys
from os.path import isdir, isfile, join



rootDir = "../../"
configDir = rootDir + "Config/"
configFile = join(configDir, "time_of_day.ini")

# required to be able to use pipeline classes
sys.path.insert(0, rootDir)
sys.path.insert(0, join(rootDir, "Code/"))

from PyQt4 import QtGui

from TimeOfDayManager import TimeOfDayManager
from TimeOfDay import TimeOfDay

if __name__ == "__main__":

    print "Starting TimeOfDay Editor"

    app = QtGui.QApplication(sys.argv)
    timeOfDay = TimeOfDay()

    if not isfile(configFile):
        print "Creating default config file"
        timeOfDay.writeDefaultFile(configFile)    

    timeOfDay.load(configFile)

    manager = TimeOfDayManager(timeOfDay)
    sys.exit(app.exec_())