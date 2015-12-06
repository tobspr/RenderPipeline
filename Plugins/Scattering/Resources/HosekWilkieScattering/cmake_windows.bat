@echo off
mkdir Windows_x32 2>nul 1>nul
cd Windows_x32
cmake -G"Visual Studio 10" ..
cmake --build . --config RelWithDebInfo
pause

