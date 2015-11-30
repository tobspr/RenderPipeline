@echo off
mkdir Windows_x64 2>nul 1>nul
cd Windows_x64
cmake -G"Visual Studio 14 Win64" ..
pause

