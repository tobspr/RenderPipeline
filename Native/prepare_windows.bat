@echo off

mkdir Windows > nul 2>&1
cd Windows

cmake ../ -G"Visual Studio 10 Win64"

pause
