
import sys


if len(sys.argv) != 3:
    print "Usage: show_voxels.py Path/To/Model.egg Path/To/Voxelized"
    sys.exit(0)


from panda3d.core import *
from direct.stdpy.file import open, join

import sys
sys.path.insert(0, "../../Code/")

from MovementController import MovementController

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
notify-level-gobj fatal 
multisamples 16
""")

import direct.directbase.DirectStart

scenePath = sys.argv[2]
eggPath = sys.argv[1]

resultFile = join(scenePath, "voxels.png")
configFile = join(scenePath, "voxels.ini")
resultEgg = eggPath


print "Loading model from", resultEgg
# model = loader.loadModel(resultEgg)
# model.flattenStrong()
# model.reparentTo(render)

print "Loading Voxel Grid from", resultFile
tex = loader.loadTexture(resultFile)
gridSize = tex.getYSize()

print "Grid size is", gridSize


# Load config, I know it's hacky, but this is only a debugging tool, so
# that's ok
with open(configFile, "r") as handle:
    configContent = handle.readlines()

extractVec3 = lambda s: Vec3(
    *([float(i) for i in s.strip().split("=")[-1].split(";")]))
gridStart = extractVec3(configContent[1])
gridEnd = extractVec3(configContent[2])
gridMid = (gridEnd - gridStart) / 2 + gridStart
voxelScale = (gridEnd - gridStart) / float(gridSize)


print gridStart, gridEnd
print "voxel scale:", voxelScale


print "Creating Debugger Box"
box = loader.loadModel("box")

boxShaderVertex = """
#version 150
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec4 p3d_Normal;
uniform sampler2D voxelGrid;
uniform int gridSize;
out vec4 color;
out float dropFragment;


void main() {
    int idx = gl_InstanceID;
    int xOffset = (idx / (gridSize*gridSize)) % gridSize;
    int yOffset = (idx / gridSize) % gridSize;
    int zOffset = idx % (gridSize);
    
    ivec3 voxelSpacePos = ivec3(xOffset, yOffset, zOffset);
    ivec2 coord = voxelSpacePos.xy + ivec2(voxelSpacePos.z * gridSize, 0);

    vec4 data = texelFetch(voxelGrid, coord, 0);
    dropFragment = 0.0;
    if ( data.w < 0.9) {
    //if ( data.y < 0.5) {
        dropFragment = 1.0;
    }

    vec3 vtxPos = p3d_Vertex.xyz + vec3(voxelSpacePos); 

    gl_Position = p3d_ModelViewProjectionMatrix * vec4(vtxPos, 1);
    float lightFactor = abs(dot(p3d_Normal.xyz, vec3(0.5,0.9,1.0)));
    color = vec4( ( abs(data.xyz*4.0 - 2.0) ), 1.0);
    // color = vec4(vec2(coord) / vec2(gridSize*gridSize, gridSize), 0, 1.0);
    //color = vec4(data.xyz, 0.25 );


}

"""

boxShaderFragment = """
#version 150
in vec4 color;
in float dropFragment;
void main() {
    if (dropFragment > 0.5) discard;
    gl_FragColor = vec4(color);
}


"""


yaxis = loader.loadModel("zup-axis")
yaxis.reparentTo(render)

base.camLens.setFov(90)
base.camLens.setNearFar(0.1, 10000)

controller = MovementController(base)
controller.setInitialPosition(gridEnd*1.3, gridMid )
controller.setup()

box.setShader(Shader.make(Shader.SLGLSL, boxShaderVertex, boxShaderFragment))
box.setShaderInput("voxelGrid", tex)
box.setShaderInput("gridSize", gridSize)
box.setInstanceCount(gridSize * gridSize * gridSize)
box.setScale(voxelScale)
box.setPos(gridStart)
box.reparentTo(render)
box.node().setFinal(True)
box.node().setBounds(OmniBoundingVolume())
render.setTransparency(TransparencyAttrib.MDual)

base.accept("f3", base.toggleWireframe)

run()
