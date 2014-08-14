
from panda3d.core import *


loadPrcFileData("", """
win-title Voxelizer - Show Voxels
sync-video #f
notify-level-pnmimage error
show-buffers #t
win-size 1600 900
texture-cache #f
model-cache 
model-cache-dir 
model-cache-textures #f
notify-level-gobj fatal 
multisamples 16
""")

import direct.directbase.DirectStart

from os.path import join

# base.disableMouse()
base.camera.setPos(100,100,100)
base.camera.lookAt(0,0,0)
base.camLens.setFov(90)
base.camLens.setNearFar(0.1, 10000)


sceneFile = "Sponza"

resultFile = join("convert", sceneFile, "voxelized/result_combined.png")

print "Loading Voxel Grid from",resultFile
tex = loader.loadTexture(resultFile)
gridSize = tex.getYSize()

print "Grid size is",gridSize

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
    if ( dot(data.xy, vec2(1)) < 0.5) {
    //if ( data.y < 0.5) {
        dropFragment = 1.0;
    }

    vec3 vtxPos = p3d_Vertex.xyz + vec3(voxelSpacePos); 

    gl_Position = p3d_ModelViewProjectionMatrix * vec4(vtxPos, 1);
    float lightFactor = abs(dot(p3d_Normal.xyz, vec3(0.5,0.9,1.0)));
    color = vec4(lightFactor*vec3(1), 1.0);
    // color = vec4(vec2(coord) / vec2(gridSize*gridSize, gridSize), 0, 1);
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

box.setShader(Shader.make(Shader.SLGLSL, boxShaderVertex, boxShaderFragment))
box.setShaderInput("voxelGrid", tex)
box.setShaderInput("gridSize", gridSize)
box.setInstanceCount(gridSize * gridSize * gridSize)
box.reparentTo(render)
box.node().setFinal(True)
box.node().setBounds(OmniBoundingVolume())
render.setTransparency(TransparencyAttrib.MDual)

base.accept("f3", base.toggleWireframe)

run()

