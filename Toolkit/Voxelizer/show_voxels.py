
import sys


if len(sys.argv) != 3:
    print "Usage: show_voxels.py Path/To/Model.egg Path/To/Voxelized"
    sys.exit(0)
scenePath = sys.argv[2]
eggPath = sys.argv[1]
showOriginalModel = False


# scenePath = "convert/GITest/voxelized"
# eggPath = "convert/GITest/Model.egg"

from panda3d.core import *
from direct.stdpy.file import open, join

import sys
sys.path.insert(0, "../../Code/")

from MovementController import MovementController



def mulVec3(a, b):
    return Vec3(a.x * b.x, a.y * b.y, a.z * b.z)


loadPrcFileData("", """
win-title Voxelizer - Show Voxels
sync-video #f
notify-level-pnmimage error
show-buffers #f
win-size 800 600
texture-cache #f
model-cache 
model-cache-dir 
model-cache-textures #f 
multisamples 16
""")

import direct.directbase.DirectStart


resultFile = join(scenePath, "voxels.png")
configFile = join(scenePath, "voxels.ini")
resultEgg = eggPath


if showOriginalModel:
    print "Loading model from", resultEgg
    model = loader.loadModel(resultEgg)
    model.flattenStrong()
    model.reparentTo(render)

print "Loading Voxel Grid from", resultFile
tex = loader.loadTexture(resultFile)

# Load config file
with open(configFile, "r") as handle:
    configContent = handle.readlines()

options = {
    "GridResolution": "int",
    "GridStart": "vec3",
    "GridEnd": "vec3",
    "StackSizeX": "int",
    "StackSizeY": "int"
}

optionValues = {}

for line in configContent:
    if len(line) > 2 and "=" in line:
        line = line.strip().split("=")
        optionName = line[0]
        optionValue = line[1]

        if optionName in options:
            optionType = options[optionName]
            parsedValue = None

            if optionType == "int":
                parsedValue = int(optionValue)
            elif optionType == "vec3":
                parsedValue = Vec3(
                    *([float(i) for i in optionValue.split(";")]))
            optionValues[optionName] = parsedValue
            print optionName, "=", parsedValue

gridStart = optionValues["GridStart"]
gridEnd = optionValues["GridEnd"]
stackSizeX = optionValues["StackSizeX"]
stackSizeY = optionValues["StackSizeY"]
gridSize = optionValues["GridResolution"]
gridDimensions = gridEnd - gridStart
gridMid = gridDimensions / 2 + gridStart
voxelScale = gridDimensions / float(gridSize)

boxShaderVertex = """
#version 150
uniform mat4 p3d_ViewProjectionMatrix;
uniform mat4 trans_model_to_world;
in vec4 p3d_Vertex;
uniform int gridSize;
uniform vec3 gridStart;
uniform vec3 gridEnd;
uniform vec3 voxelSize;
uniform vec3 direction;
out vec3 texcoord;
out float dropFragment;

void main() {
    int idx = int(gl_InstanceID);

    vec4 modelPos = p3d_Vertex;
    modelPos.xyz -= idx * -direction.xyz;
    vec4 worldPos = trans_model_to_world * modelPos;
    //worldPos.xyz += idx * direction * voxelSize;
    //worldPos+=0.0001;
    gl_Position = p3d_ViewProjectionMatrix * worldPos;
    texcoord = (worldPos.xyz - gridStart) / (gridEnd - gridStart);
    texcoord.z += 0.001;


}

"""

boxShaderFragment = """
#version 150
in vec3 texcoord;
uniform sampler2D voxelGrid;
uniform int gridSize;
uniform int stackSizeX;

void main() {
    

    ivec3 voxelSpaceCoord = ivec3(texcoord.xyz * float(gridSize));
    ivec2 lookupCoord = voxelSpaceCoord.xy;
    lookupCoord += ivec2(voxelSpaceCoord.z % stackSizeX, voxelSpaceCoord.z / stackSizeX) * gridSize;
    vec4 lookupResult = texelFetch(voxelGrid, lookupCoord, 0);

    if (lookupResult.w < 0.5) discard;

    gl_FragColor = vec4( lookupResult.xyz, 1);
}


"""


yaxis = loader.loadModel("zup-axis")
yaxis.reparentTo(render)


base.camLens.setFov(90)
base.camLens.setNearFar(0.1, 5000)

controller = MovementController(base)
controller.setInitialPosition(gridEnd * 1.3, gridMid)
controller.setup()

render.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullNone), 1000000)

dirs = [
    (Vec3(0, 0, 1), Vec3(0, 90, 0), Vec3(0, 1, 0)),
    (Vec3(0, 1, 0), Vec3(0, 0, 0), Vec3(0, 0, 0)),
    (Vec3(1, 0, 0), Vec3(90, 0, 0), Vec3(0, 0, 0)),
]

for direction, hpr, posOffs in dirs:

    c = CardMaker("cm")
    c.setFrame(0, 1, 0, 1)
    cm = render.attachNewNode(c.generate())
    cm.setHpr(hpr)
    cm.setPos(posOffs +  Vec3(0.001))
    cm.flattenStrong()
    cm.setScale( mulVec3(gridDimensions, Vec3(1)-direction) + mulVec3(voxelScale, direction) )
    cm.setPos(gridStart)
    cm.setShader(
        Shader.make(Shader.SLGLSL, boxShaderVertex, boxShaderFragment))
    cm.setShaderInput("voxelGrid", tex)
    cm.setShaderInput("gridSize", int(gridSize))
    cm.setShaderInput("gridStart", gridStart)
    cm.setShaderInput("gridEnd", gridEnd)
    cm.setShaderInput("voxelSize", voxelScale)
    cm.setShaderInput("direction", direction)
    cm.setShaderInput("stackSizeX", stackSizeX)
    # box.setInstanceCount(gridSize * gridSize * gridSize)
    cm.setInstanceCount(gridSize + 1)
    cm.node().setFinal(True)
    cm.node().setBounds(OmniBoundingVolume())

base.run()
