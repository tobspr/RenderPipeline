@echo off

"./mitsuba/mitsuba" scene.xml
echo ""
echo Rendering done
echo ""
echo ""
echo ""
"./mitsuba/mtsutil" tonemap scene.exr
del scene.exr
del mitsuba.*.log
pause
