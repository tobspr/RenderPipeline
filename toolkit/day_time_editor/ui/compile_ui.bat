@echo off

rem Adjust the path to match your PyQt4 installation
rem SET PYQTPATH="E:\ProgrammeTemp\PyQT\Lib\site-packages\PyQt4"
SET PYQTPATH="C:\Projekte\PythonInc\PyQt4"

python "%PYQTPATH%\uic\pyuic.py" --from-imports main_window.ui -o main_window_generated.py
python "%PYQTPATH%\uic\pyuic.py" --from-imports point_insert.ui -o point_insert_dialog_generated.py
"%PYQTPATH%\pyrcc4.exe" -py3 resources.qrc -o resources_rc.py

pause
