@echo off
set PANDAPATH=%~dp0panda3d
set PATH=%PANDAPATH%\bin;%PANDAPATH%;%PATH%
set PYTHONPATH=%PANDAPATH%\;%PYTHONPATH%
echo Running Panda3D from "%PANDAPATH%"
"%PANDAPATH%\python\ppython.exe" -B application/main.py
pause
