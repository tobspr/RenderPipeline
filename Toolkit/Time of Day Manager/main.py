import sys
from os.path import isdir, isfile, join

rootDir = "../../"
configDir = rootDir + "Config/"
configFile = join(configDir, "time_of_day.ini")


if not isdir(rootDir):
    print "Root directory does not exist!"
    sys.exit(0)

if not isdir(configDir):
    print "Config directory does not exist!"
    sys.exit(0)

# required to be able to use pipeline classes
sys.path.insert(0, rootDir)
sys.path.insert(0, join(rootDir, "Code/"))

from PyQt4 import QtGui

from TimeOfDayWindow import TimeOfDayWindow
from TimeOfDay import TimeOfDay

if __name__ == "__main__":

    print "Starting TimeOfDay Editor"

    app = QtGui.QApplication(sys.argv)
    timeOfDay = TimeOfDay()

    if not isfile(configFile):
        print "Creating default config file"
        timeOfDay.save(configFile)    

    timeOfDay.load(configFile)

    manager = TimeOfDayWindow(timeOfDay)
    manager.setSavePath(join(configDir, "time_of_day.ini"))
    manager.show()

    
    sys.exit(app.exec_())