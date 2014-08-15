

from panda3d.core import *

import sys
import time
from os import listdir, makedirs
from direct.stdpy.file import join, isfile, isdir, open
from direct.showbase.ShowBase import ShowBase
import random


def mulVec3(a, b):
    return Vec3(a.x * b.x, a.y * b.y, a.z * b.z)


DEBUG_MODE = False

defaultVertexShader = """
#version 150
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 trans_model_to_world;
in vec4 p3d_Vertex;
in vec4 p3d_Normal;
out vec4 color;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    color.w = 1.0;
    vec4 normalWorld = trans_model_to_world * vec4(p3d_Normal.xyz, 0);
    color.xyz = normalize(normalWorld.xyz) * 0.25 + 0.5;

    if (length(p3d_Normal.xyz) < 0.9) {
        color.w = 0.0;
    }
    //color.xyz = vec3(0,0,1);
}
"""
defaultFragmentShader = """
#version 150
in vec4 color;
void main() {
    if (color.w < 0.5) discard;
    gl_FragColor = color;
}
"""

defaultShader = Shader.make(
    Shader.SLGLSL, defaultVertexShader, defaultFragmentShader)


class VoxelizerShowbase(ShowBase):

    def __init__(self):

        loadPrcFileData("", """
        win-title Voxelizer
        sync-video #f
        notify-level-pnmimage error
        show-buffers #t
        win-size 100 100
        texture-cache #f
        model-cache
        model-cache-dir
        model-cache-textures #f
        notify-level-gobj fatal
        window-type offscreen
        gl-finish #t
        """)

        ShowBase.__init__(self)
        self.disableMouse()
        self.layerCamera = None
        self.addTask(self.update, "update")
        self.renderLens = OrthographicLens()

        # Generate the compute shader nodes, required to execute the compute
        # shaders
        self.generateNode = NodePath("GenerateVoxelsNode")
        self.generateNode.setShader(
            Shader.loadCompute(Shader.SLGLSL, "generate_voxels_compute_shader.glsl"))
        self.combineNode = NodePath("CombineVoxels")
        self.combineNode.setShader(
            Shader.loadCompute(Shader.SLGLSL, "combine_directions_compute_shader.glsl"))
        self.processNode = NodePath("ProcessVoxels")
        self.processNode.setShader(
            Shader.loadCompute(Shader.SLGLSL, "remove_lonely_voxels_compute_shader.glsl"))

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

        # Create ramdisk, that's faster
        vfs = VirtualFileSystem.getGlobalPtr()

        if DEBUG_MODE:
            vfs.mount(VirtualFileMountSystem("temp/"), tempPath, 0)
        else:
            vfs.mount(VirtualFileMountRamdisk(), tempPath, 0)

        logCallback(10, "Loading model from disk ..")
        # Reset model path first
        getModelPath().clearLocalValue()

        # Now add the file directory to the model path, not sure why it
        # it can't find the textures otherwise
        getModelPath().prependDirectory(sourceDirectory)

        try:
            model = loader.loadModel(filename, noCache=True)
        except Exception, msg:
            logCallback(0, "Failed to load model!", True)
            logCallback(0, "Message: " + str(msg), True)
            return False

        model.setShader(defaultShader)

        # Get min/max bounds for the model
        minBounds, maxBounds = model.getTightBounds()

        gridResolution = options["gridResolution"]

        # Add some border to the voxel grid
        minBounds -= Vec3(options["border"])
        maxBounds += Vec3(options["border"])
        gridSize = maxBounds - minBounds
        gridCenter = minBounds + gridSize * 0.5
        voxelSize = gridSize / float(gridResolution)
        logCallback(
            20, "Bounds are " + vectorToStr(minBounds) + " to " + vectorToStr(maxBounds))
        logCallback(20, "Voxel size is " + vectorToStr(voxelSize))

        start = time.time()

        datafile = "GridResolution=" + str(gridResolution) + "\n"
        datafile += "GridStart=" + \
            str(minBounds.x) + ";" + str(minBounds.y) + \
            ";" + str(minBounds.z) + "\n"
        datafile += "GridEnd=" + \
            str(maxBounds.x) + ";" + str(maxBounds.y) + \
            ";" + str(maxBounds.z) + "\n"

        if not isdir(destination):
            makedirs(Filename.fromOsSpecific(destination).toOsGeneric() )

        with open(join(destination, "voxels.ini"), "w") as handle:
            handle.write(datafile)

        self.layerBuffer = base.win.makeTextureBuffer(
            "Layer", gridResolution, gridResolution)
        self.layerTexture = self.layerBuffer.getTexture()
        self.layerBuffer.setSort(-100)
        self.layerCamera = self.makeCamera(self.layerBuffer)
        self.layerScene = NodePath("LayerScene")
        self.layerCamera.reparentTo(self.layerScene)
        self.layerCamera.setPos(10, 10, 10)
        self.layerCamera.node().setLens(self.renderLens)
        self.layerCamera.lookAt(0, 0, 0)

        self.layerBuffer.setClearColor(Vec4(0.5, 0.5, 0.5, 0.5))

        model.reparentTo(self.layerScene)

        cullModes = [
            ("frontface", CullFaceAttrib.MCullClockwise),
            ("backface", CullFaceAttrib.MCullCounterClockwise),
        ]

        attributeCounter = 500

        directions = [
            ("x", Vec3(1, 0, 0), Vec3(gridSize.y, gridSize.z, voxelSize.x)),
            ("y", Vec3(0, 1, 0), Vec3(gridSize.x, gridSize.z, voxelSize.y)),
            ("z", Vec3(0, 0, 1), Vec3(gridSize.x, gridSize.y, voxelSize.z))
        ]
        self.renderLens.setNearFar(0, 1000)
        self.renderLens.setFilmSize(20, 20)

        self.directionTextures = {}

        progress = 0

        for dirName, direction, filmSize in directions:
            logCallback(30 + progress, "Rendering direction " + dirName)
            progress += 8
            basePosition = mulVec3(gridCenter, (Vec3(1) - direction))
            basePosition += mulVec3(minBounds, direction)
            lookAt = gridCenter - direction * 100000.0
            self.renderLens.setFilmSize(filmSize.x, filmSize.y)
            self.renderLens.setNearFar(0, filmSize.z)

            for i in xrange(gridResolution):
                cameraPosition = basePosition + \
                    mulVec3(voxelSize, direction * float(i + 1))
                self.layerCamera.setPos(cameraPosition)
                self.layerCamera.lookAt(lookAt)
                for mode, attrib in cullModes:
                    model.setAttrib(
                        CullFaceAttrib.make(attrib), attributeCounter)
                    attributeCounter += 1
                    self.graphicsEngine.renderFrame()

                    # This is the main bottleneck. I have to figure out how to load
                    # a 2d texture from ram
                    self.graphicsEngine.extract_texture_data(
                        self.layerTexture, self.win.getGsg())
                    self.layerTexture.write(
                        tempPath + dirName + "_" + mode + "_" + str(i).zfill(5) + ".png")

            # Now reconstruct voxels
            logCallback(30 + progress, "Evaluating direction " + dirName)
            progress += 11

            frontfaceTex = TexturePool.load2dTextureArray(
                tempPath + dirName + "_frontface_#####.png")
            backfaceTex = TexturePool.load2dTextureArray(
                tempPath + dirName + "_backface_#####.png")

            # We have to use a 2d texture for storage, as we can't use image Load/Store
            # for a 2d Texture
            storage = Texture("storage")
            storage.setup2dTexture(
                gridResolution * gridResolution, gridResolution,
                Texture.TFloat, Texture.FRgba16)

            # Generate voxel grid
            self.generateNode.setShaderInput("frontfaceTex", frontfaceTex)
            self.generateNode.setShaderInput("backfaceTex", backfaceTex)
            self.generateNode.setShaderInput("gridSize", gridResolution)
            self.generateNode.setShaderInput("destination", storage)
            sattr = self.generateNode.get_attrib(ShaderAttrib)
            self.graphicsEngine.dispatch_compute(
                (gridResolution / 16, gridResolution / 16, 1), sattr, self.win.get_gsg())
            self.directionTextures[dirName] = storage

            # Save result texture
            if DEBUG_MODE:
                self.graphicsEngine.extract_texture_data(
                    storage, self.win.getGsg())

                # PNMImage does not support writing to a VFS :( so we have to
                # store it in the working directory
                storage.write("result_" + dirName + ".png")


        logCallback(80, "Combining directions ..")

        # finally, combine all textures
        resultTexture = Texture("result")
        resultTexture.setup2dTexture(
            gridResolution * gridResolution, gridResolution,
            Texture.TFloat, Texture.FRgba16)

        self.combineNode.setShaderInput(
            "directionX", self.directionTextures["x"])
        self.combineNode.setShaderInput(
            "directionY", self.directionTextures["y"])
        self.combineNode.setShaderInput(
            "directionZ", self.directionTextures["z"])
        self.combineNode.setShaderInput("destination", resultTexture)
        self.combineNode.setShaderInput("gridSize", gridResolution)
        sattr = self.combineNode.get_attrib(ShaderAttrib)
        self.graphicsEngine.dispatch_compute(
            (gridResolution / 8, gridResolution / 8, gridResolution / 8), sattr, self.win.get_gsg())

        logCallback(85, "Post-Processing generated voxels ..")

        # now, do some further processing
        processedTexture = Texture("result")
        processedTexture.setup2dTexture(
            gridResolution * gridResolution, gridResolution,
            Texture.TFloat, Texture.FRgba16)

        self.processNode.setShaderInput("destination", processedTexture)
        self.processNode.setShaderInput("source", resultTexture)
        self.processNode.setShaderInput("gridSize", gridResolution)
        self.processNode.setShaderInput(
            "rejectionFactor", float(options["rejectionFactor"]) + 0.5)
        self.processNode.setShaderInput(
            "fillVolumes", bool(options["fillVolumes"]))
        self.processNode.setShaderInput(
            "discardInvalidVoxels", bool(options["discardInvalidVoxels"]))
        sattr = self.processNode.get_attrib(ShaderAttrib)
        self.graphicsEngine.dispatch_compute(
            (gridResolution / 8, gridResolution / 8, gridResolution / 8), sattr, self.win.get_gsg())


        self.graphicsEngine.extract_texture_data(
            processedTexture, self.win.getGsg())
        
        if DEBUG_MODE:
            self.graphicsEngine.extract_texture_data(
                resultTexture, self.win.getGsg())

        store = join(destination, "voxels.png")
        logCallback(90, "Saving voxel grid to '" + store + "'..")
        processedTexture.write(store)

        if DEBUG_MODE:
            resultTexture.write(join(destination, "unprocessedVoxels.png"))

        logCallback(99, "Cleanup ..")
        self.graphicsEngine.removeWindow(self.layerBuffer)
        self.layerScene.removeNode()
        self.layerCamera.removeNode()
        end = time.time()
        durationMs = round((end - start) * 1000.0, 3)

        logCallback(100, "Converted in " + str(durationMs) + " ms!")
        return True

    def update(self, task):
        # if self.layerCamera is not None:
            # self.layerCamera.setPos(self.layerCamera.getPos() * 1.0001)
        return task.cont


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

    gridResolution = 128
    rejectionFactor = 2.5
    fillVolumes = False
    border = LPoint3f(1)

    sourceDir = "convert/"
    filesToConvert = recursiveFindFiles(sourceDir)

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
            "rejectionFactor": rejectionFactor,
            "fillVolumes": fillVolumes,
            "border": border,
            "discardInvalidVoxels": False
        })
