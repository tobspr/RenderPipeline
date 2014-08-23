

from panda3d.core import *

import sys
sys.path.insert(0, "../../")

from Code.RenderTarget import RenderTarget
from Code.Globals import Globals
from Code.TextureCleaner import TextureCleaner

import time
from os import listdir, makedirs
from direct.stdpy.file import join, isfile, isdir, open
from direct.showbase.ShowBase import ShowBase
import random
import math


def mulVec3(a, b):
    return Vec3(a.x * b.x, a.y * b.y, a.z * b.z)


DEBUG_MODE = False

defaultVertexShader = """
#version 150

uniform mat4 p3d_ViewProjectionMatrix;
uniform mat4 trans_model_to_world;
in vec4 p3d_Vertex;
in vec4 p3d_Normal;
in vec2 p3d_MultiTexCoord0;
out vec4 color;
out vec3 normal;
out vec4 positionWorld;
out vec2 texc;

void main() {
    positionWorld = trans_model_to_world * p3d_Vertex; 
    gl_Position = p3d_ViewProjectionMatrix * positionWorld;
    color.w = 1.0;
    vec4 normalWorld = trans_model_to_world * vec4(p3d_Normal.xyz, 0);
    normal = normalWorld.xyz;
    color.xyz = normalize(normalWorld.xyz) * 0.25 + 0.5;
    texc = p3d_MultiTexCoord0;
}
"""


defaultGeometryShader = """
#version 400

layout(triangles) in;
layout(triangle_strip, max_vertices=3) out;

in vec4 color[3];
in vec3 normal[3];
in vec4 positionWorld[3];
in vec2 texc[3];
uniform ivec3 direction;
out vec4 fragmentColor;
out vec4 geomPositionWorld;
out vec2 texcoord;

void main() {

    
    vec3 combinedNormal = normalize(normal[0] + normal[1] + normal[2]);
    vec3 absNormal = abs(combinedNormal);
    bool renderVertices = false;

    if (direction == ivec3(1,0,0)) {
        if (absNormal.x >= max(absNormal.y, absNormal.z)) {
            // X is longest component
            renderVertices = true;
        }
    } else if (direction == ivec3(0,1,0)) {
        if (absNormal.y >= max(absNormal.x, absNormal.z)) {
            // Y is longest component
            renderVertices = true;
        }
    } else if (direction == ivec3(0,0,1)) {
        if (absNormal.z >= max(absNormal.x, absNormal.y)) {
            // Z is longest component
            renderVertices = true;
        }
    }

    if (renderVertices) {
        for(int i=0; i<gl_in.length(); i++)
        {
            gl_Position = gl_in[i].gl_Position;
            fragmentColor = color[i];
            geomPositionWorld = positionWorld[i];
            texcoord = texc[i];
            EmitVertex();
        }
        EndPrimitive();    
    }
}

"""


defaultFragmentShader = """
#version 400
#extension GL_ARB_shader_image_load_store : enable
in vec4 fragmentColor;
in vec4 geomPositionWorld;
in vec2 texcoord;

uniform sampler2D p3d_Texture0;

uniform vec3 gridStart;
uniform vec3 gridEnd;
uniform int gridResolution;
uniform int stackSizeX;

uniform writeonly image2D voxelStorageGrid;

out vec4 result;
void main() {
    //if (color.w < 0.5) discard;

    vec3 voxelSpacePos = (geomPositionWorld.xyz-gridStart) / (gridEnd - gridStart);
    ivec3 voxelCoords = ivec3(voxelSpacePos * float(gridResolution));

    ivec2 texcoords = voxelCoords.xy;
    ivec2 stackOffset = ivec2(voxelCoords.z % stackSizeX, voxelCoords.z / stackSizeX);
    texcoords += stackOffset * gridResolution;

    vec3 diffuse = texture(p3d_Texture0, texcoord).rgb;

    imageStore(voxelStorageGrid, texcoords, vec4(diffuse, 1));
    result = vec4(1);
}
"""


defaultShader = Shader.make(
    Shader.SLGLSL, defaultVertexShader, defaultFragmentShader, defaultGeometryShader)


class VoxelizerShowbase(ShowBase):

    def __init__(self):

        loadPrcFileData("", """
        win-title Voxelizer
        sync-video #f
        notify-level-pnmimage error
        show-buffers #t
        win-size 800 800
        window-type offscreen
        framebuffer-srgb #f
        textures-power-2 none
        gl-finish #f
        gl-force-no-error #t
        gl-check-errors #f
        gl-force-no-flush #t
        gl-force-no-scissor #t
        gl-debug #f

        """)

        ShowBase.__init__(self)
        Globals.load(self)
        self.disableMouse()
        self.renderLens = OrthographicLens()
        # self.renderLens = PerspectiveLens()
        # self.renderLens.setFov(90)
        self.cam.node().setLens(self.renderLens)
        self.accept("f3", self.toggleWireframe)
        

        # Generate the compute shader nodes, required to execute the compute
        # shaders
        self.combineNode = NodePath("CombineVoxels")
        self.combineNode.setShader(
            Shader.loadCompute(Shader.SLGLSL, "combine_directions_compute_shader.glsl"))
    def _logCallback(self, percent, message, isError=False):
        print percent, message

    def voxelize(self, filename, sourceDirectory, destination, options, logCallback=None):
        """ Voxelizes the geometry from <filename> """

        if logCallback is None:
            logCallback = self._logCallback

        vectorToStr = lambda v: "[" + str(round(v.x, 2)) + ", " + str(
            round(v.y, 2)) + ", " + str(round(v.z, 2)) + "]"

        # Store the temporary files in a random path, otherwise panda caches it
        tempPath = "temp/" + str(random.randint(10000000, 99999999)) + "/"

        # Create the temp folders
        # If debug mode is enabled, files will be written to disk.
        # Otherwise a ramdisk is used
        vfs = VirtualFileSystem.getGlobalPtr()
        if DEBUG_MODE:
            if not isdir("temp/"):
                try:
                    makedirs("temp/")
                except Exception, msg:
                    logCallback(5, "Could not create temp directory!", True)

            vfs.mount(VirtualFileMountSystem("temp/"), tempPath, 0)
        else:
            vfs.mount(VirtualFileMountRamdisk(), tempPath, 0)

        logCallback(10, "Loading model from disk ..")

        # Reset model path
        getModelPath().clearLocalValue()

        # Now add the file directory to the model path, not sure why
        # it can't find the textures otherwise
        # getModelPath().prependDirectory(sourceDirectory)

        try:
            model = loader.loadModel(filename)
        except Exception, msg:
            logCallback(0, "Failed to load model!", True)
            logCallback(0, "Message: " + str(msg), True)
            return False

        # Set the voxelization shader
        model.setShader(defaultShader)

        # Compute stack size
        gridResolution = options["gridResolution"]
        stackX = int(math.ceil(math.sqrt(gridResolution)))
        # Stack should be a power of two:
        stackX = 2 ** (stackX.bit_length())

        stackRows = int(math.ceil(gridResolution / float(stackX)))
        logCallback(15, "Stack size is " + str(stackX) + "x" + str(stackRows))

        # Get min/max bounds for the model
        minBounds, maxBounds = model.getTightBounds()

        # Add some border to the voxel grid
        minBounds -= Vec3(options["border"])
        maxBounds += Vec3(options["border"])

        # Compute useful variables
        gridSize = maxBounds - minBounds
        gridCenter = minBounds + gridSize * 0.5
        voxelSize = gridSize / float(gridResolution)

        logCallback(
            20, "Bounds are " + vectorToStr(minBounds) + " to " + vectorToStr(maxBounds))
        logCallback(20, "Voxel size is " + vectorToStr(voxelSize))

        totalStart = time.time()

        datafile = "GridResolution=" + str(gridResolution) + "\n"
        datafile += "GridStart=" + \
            str(minBounds.x) + ";" + str(minBounds.y) + \
            ";" + str(minBounds.z) + "\n"
        datafile += "GridEnd=" + \
            str(maxBounds.x) + ";" + str(maxBounds.y) + \
            ";" + str(maxBounds.z) + "\n"
        datafile += "StackSizeX=" + str(stackX) + "\n"
        datafile += "StackSizeY=" + str(stackRows) + "\n"

        if not isdir(destination):
            makedirs(Filename.fromOsSpecific(destination).toOsGeneric())

        logCallback(22, "Writing voxels.ini to '" + join(destination, "voxels.ini") + "'")

        with open(join(destination, "voxels.ini"), "w") as handle:
            handle.write(datafile)

        self.voxelTarget = RenderTarget("Render Voxels")
        self.voxelTarget.addColorTexture()
        self.voxelTarget.setSize(gridResolution, gridResolution)
        self.voxelTarget.prepareSceneRender()
        self.voxelTarget.setClearColor(True, Vec4(0))
        self.voxelTarget.removeQuad()

        model.flattenStrong()        
        

        directions = [
            ("x", Vec3(1, 0, 0), Vec3(gridSize.y, gridSize.z, gridSize.x)),
            ("y", Vec3(0, 1, 0), Vec3(gridSize.x, gridSize.z, gridSize.y)),
            ("z", Vec3(0, 0, 1), Vec3(gridSize.x, gridSize.y, gridSize.z)),
        ]

        directionTextures = {}

        model.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullNone), 100)
        model.setAttrib(DepthTestAttrib.make(DepthTestAttrib.MNone), 200)
        model.node().setBounds(OmniBoundingVolume())
        model.node().setFinal(True)

        for node in model.findAllMatches("**"):
            node.node().setBounds(OmniBoundingVolume())
            node.node().setFinal(True)

        self.layerScene = render.attachNewNode("model")
        model.reparentTo(self.layerScene)

        progress = 0

        for dirName, direction, filmSize in directions:

            # Create a texture where the result will be stored
            dirTexture = Texture("Direction")
            dirTexture.setup2dTexture(gridResolution * stackX, gridResolution * stackRows,
                                      Texture.TFloat, Texture.FRgba8)

            # We have to clear the texture, otherwise it contains random stuff
            TextureCleaner.clearTexture(dirTexture, Vec4(0, 0, 0, 0))
            logCallback(30 + progress, "Rendering direction " + dirName)
            progress += 19

            # Set the camera to the end of the voxel grid, and make it look
            # *through* the grid
            basePosition = mulVec3(gridCenter, (Vec3(1) - direction))
            basePosition -= mulVec3(maxBounds, direction)
            self.renderLens.setFilmSize(filmSize.x, filmSize.y)
            
            # Theoretically this should work
            # self.renderLens.setNearFar(0, filmSize.z)

            # But, it does not work without this!
            self.renderLens.setNearFar(-1000000, 1000000)

            self.camera.setPos(basePosition)
            self.camera.lookAt(gridCenter)
            self.cam.setPos(0, 0, 0)
            self.cam.setHpr(0, 0, 0)

            # Set the necessary shader inputs for generating the voxels
            render.setShaderInput(
                "direction", LVecBase3i(
                    int(direction.x),
                    int(direction.y),
                    int(direction.z)))
            render.setShaderInput("voxelStorageGrid", dirTexture)
            render.setShaderInput("gridResolution", LVecBase3i(gridResolution))
            render.setShaderInput("gridStart", minBounds)
            render.setShaderInput("gridEnd", maxBounds)
            render.setShaderInput("voxelSize", voxelSize)
            render.setShaderInput("stackSizeX", LVecBase3i(stackX))
            self.graphicsEngine.renderFrame()

            # In case of debug mode, write the texture to disk
            if DEBUG_MODE:
                self.graphicsEngine.extract_texture_data(
                    dirTexture, self.win.getGsg())
                dirTexture.write("Direction-" + dirName + ".png")

            directionTextures[dirName] = dirTexture

        logCallback(80, "Combining directions ..")

        # finally, combine all textures
        resultTexture = Texture("result")
        resultTexture.setup2dTexture(
            gridResolution * stackX, gridResolution * stackRows,
            Texture.TFloat, Texture.FRgba8)

        self.combineNode.setShaderInput(
            "directionX", directionTextures["x"])
        self.combineNode.setShaderInput(
            "directionY", directionTextures["y"])
        self.combineNode.setShaderInput(
            "directionZ", directionTextures["z"])
        self.combineNode.setShaderInput("destination", resultTexture)
        sattr = self.combineNode.get_attrib(ShaderAttrib)
        self.graphicsEngine.dispatch_compute(
            (gridResolution*stackX / 16, gridResolution*stackRows / 16, 1), sattr, self.win.get_gsg())


        store = join(destination, "voxels.png")
        logCallback(90, "Saving voxel grid to '" + store + "', this might take a while ..")
        self.graphicsEngine.extract_texture_data(
            resultTexture, self.win.getGsg())

        resultTexture.write(store)

        logCallback(99, "Cleanup ..")
        self.voxelTarget.deleteBuffer()
        self.layerScene.removeNode()

        durationMs = round((time.time() - totalStart) * 1000.0, 3)

        logCallback(100, "Converted in " + str(durationMs) + " ms!")
        return True


def recursiveFindFiles(currentDir):
    """ Collects all .egg and .bam files recursively """
    result = []
    for f in listdir(currentDir):
        fullpath = join(currentDir, f)

        if isfile(fullpath) and f.split(".")[-1].lower().strip() in ["bam", "egg"]:
            result.append((fullpath, currentDir))
        elif isdir(fullpath):
            result += recursiveFindFiles(fullpath)
    return result


if __name__ == "__main__":

    print "Voxelizer v0.001 // by tobspr"

    gridResolution = 256
    border = LPoint3f(1)
    sourceDir = "convert/"
    filesToConvert = recursiveFindFiles(sourceDir)

    # filesToConvert = [
    #     ("../../Demoscene.ignore/sponza.egg.bam", "../../Demoscene.ignore/")
    # ]

    if len(filesToConvert) < 1:
        print "Early exit: No files to convert found!"
        sys.exit(0)

    voxelizer = VoxelizerShowbase()

    print len(filesToConvert), "file[s] to voxelize found"

    for f, d in filesToConvert:
        # Convert each file
        dest = join(d, "voxelized")
        if not isdir(dest):
            makedirs(dest)
        voxelizer.voxelize(f, d, dest, {
            "gridResolution": gridResolution,
            "border": border,
        })
