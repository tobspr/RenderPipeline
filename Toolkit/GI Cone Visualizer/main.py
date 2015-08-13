

import sys
sys.path.insert(0, "../../")

from Code.GUI.BetterSlider import BetterSlider
from Code.GUI.BetterOnscreenText import BetterOnscreenText
from Code.Globals import Globals


from panda3d.core import *

import direct.directbase.DirectStart
from direct.gui.DirectSlider import DirectSlider
Globals.load(base)

samples = 64
smileys = []

for i in xrange(samples):
    smiley = loader.loadModel("smiley")
    smiley.setScale(0.5)
    smiley.flattenStrong()
    smiley.reparentTo(render)
    smileys.append(smiley)


valuesV = {}
slidersV = {}
labelsV = {}

import math

def updateCones():

    startDistance = valuesV["startDistance"]
    stepRatio = valuesV["stepRatio"]
    coneRatio = valuesV["coneRatio"]
    initialConeRadius = valuesV["initialConeRad"]

    directionStep = Vec3(0,0,1)
    currentDistance = float(startDistance)
    currentConeRadius = float(initialConeRadius)

    for i in xrange(samples):
        currentConeRadius *= stepRatio
        currentDistance += currentConeRadius * coneRatio

        currentPos = directionStep * currentDistance
        currentMip = currentConeRadius * 0.1
        mipScale = max(0.0, min(1.0, currentMip / 10.0)) 

        smiley = smileys[i]
        smiley.setScale(currentConeRadius)
        smiley.setColorScale(mipScale, 1.0 - mipScale, 0, 1)
        smiley.setPos(currentPos)



# GLSL REFERENCE:
"""

vec4 traceConeWithCollisions(GIData data, vec3 start, vec3 direction, 
int iterations, float stepRatio, float coneRatio, float startDistance, float initialConeRadius) {

    vec3 directionStep = normalize(direction) * data.normalizationFactor;
    vec4 result = vec4(0);

    float currentDistance = startDistance;
    float currentConeRadius = initialConeRadius;

    for (int i = 0; i < iterations; i++) {
        currentConeRadius *= stepRatio; 
        currentDistance += currentConeRadius * coneRatio;
        vec3 currentPos = start + directionStep * currentDistance;
        float currentMip = clamp(log2( currentConeRadius ) * 2.0, 0.0, 8.0);
        vec4 currentVal = textureLod(data.voxels, currentPos, currentMip * 1.5 );
        result += (1.0-result.w) * currentVal;
    }
    return result;
}

"""


values = [
    ("stepRatio", 1.01, 2.0, 1.05),
    ("coneRatio", 0.01, 5.0, 1.1),
    ("startDistance", -5.0, 5.0, 1.0),
    ("initialConeRad", 0.01, 5.0, 0.5),
]

def setVal(name):
    valuesV[name] = slidersV[name].getValue()
    labelsV[name]._node.setText(str(round(valuesV[name], 3)))
    updateCones()

sliders = pixel2d.attachNewNode("sliderGUI")
y = 20
for name, minv, maxv, v in values:
    slider = BetterSlider(170,30+y, sliders, size=300, minValue=minv, maxValue=maxv,
                     value=v, pageSize=0.001, callback=setVal, extraArgs=[name])
    sliderLable = BetterOnscreenText(text=name, parent=sliders, x=10, y=35+y, size=15)
    sliderValLable = BetterOnscreenText(text="..", parent=sliders, x=120, y=35+y, size=15, color=Vec4(0.7,0.0,0.0,1.0), mayChange=True)
    y += 40

    valuesV[name] = minv
    slidersV[name] = slider
    labelsV[name] = sliderValLable

run()
