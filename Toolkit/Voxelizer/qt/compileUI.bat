@echo off
echo You don't need to use this

echo Compiling UI
ppython "E:\Projects\Brainz stuff\Shared\PyQt4\uic\pyuic.py" -o main.py main.ui 

echo Comiling Resources
"E:\Projects\Brainz stuff\Shared\PyQt4\pyrcc4.exe" -o resources_rc.py resources.qrc

pause

