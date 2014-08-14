import sys
import shutil
import time
from panda3d.core import *
from os import listdir, makedirs
from os.path import join, isfile, isdir
from direct.showbase.ShowBase import ShowBase


def mulVec3(a, b):
    return Vec3(a.x * b.x, a.y * b.y, a.z * b.z)


defaultVertexShader = """
#version 150
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
out vec4 color;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    color = vec4(abs(p3d_Vertex.xyz)*0.05, 1.0);
    color.w = 1.0;
    color.xyz = vec3(1);
}
"""
defaultFragmentShader = """
#version 150
in vec4 color;
void main() {
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
        notify-level-gobj error
        """)
        ShowBase.__init__(self)
        self.disableMouse()
        self.layerCamera = None
        self.addTask(self.update, "update")
        self.renderLens = OrthographicLens()
        self.generateNode = NodePath("GenerateVoxelsNode")
        self.generateNode.setShader(Shader.loadCompute(Shader.SLGLSL, "generate_voxels_compute_shader.glsl"))
        self.combineNode = NodePath("CombineVoxels")
        self.combineNode.setShader(Shader.loadCompute(Shader.SLGLSL, "combine_directions_compute_shader.glsl"))


    def voxelize(self, filename, sourceDirectory, destination):



        gridResolution = 128

        print "Voxelizer::Voxelizing", filename
        print "Voxelizer::Will store result at", dest

        # Remove temp path
        if isdir("temp"):
            shutil.rmtree("temp")
            time.sleep(0.1)

        makedirs("temp")

        # Reset model path first
        getModelPath().clearLocalValue()

        # Now add the file directory to the model path, not sure why it
        # it can't find the textures otherwise
        getModelPath().prependDirectory(sourceDirectory)

        try:
            model = loader.loadModel(filename, noCache=True)
        except Exception, msg:
            print "Failed to load model!"
            print "Message:", msg
            return False

        model.setShader(defaultShader)

        # Get min/max bounds for
        minBounds, maxBounds = model.getTightBounds()

        # Add some border to the voxel grid
        border = LPoint3f(1)
        minBounds -= border
        maxBounds += border
       


        gridSize = maxBounds - minBounds
        gridCenter = minBounds + gridSize * 0.5
        voxelSize = gridSize / float(gridResolution)
        print "Voxelizer::loaded model, now converting .."
        print "Voxelizer::Bounds are", minBounds, "to", maxBounds
        print "Voxelizer::Voxel size is", voxelSize
        print "Voxelizer::Grid center is", gridCenter
        print "Voxelizer::Grid size is", gridSize

        datafile = "GridResolution=" + str(gridResolution)+ "\n"
        datafile+= "GridStart=" + str(minBounds.x) + ";" + str(minBounds.y) + ";" + str(minBounds.z) + "\n"
        datafile+= "GridEnd=" + str(maxBounds.x) + ";" + str(maxBounds.y) + ";" + str(maxBounds.z) + "\n"

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

        self.layerBuffer.setClearColor(Vec4(1, 0, 0, 1))

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

        for dirName, direction, filmSize in directions:
            print "Rendering direction", dirName
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
                # self.taskMgr.step()
                # print "Rendering layer",i, "pos=",cameraPosition

                for mode, attrib in cullModes:
                    model.setAttrib(
                        CullFaceAttrib.make(attrib), attributeCounter)
                    attributeCounter += 1
                    self.graphicsEngine.renderFrame()

                    self.graphicsEngine.extract_texture_data(
                        self.layerTexture, self.win.getGsg())
                    self.layerTexture.write(
                        "temp/" + dirName + "_" + mode + "_" + str(i).zfill(5) + ".png")

            # Now reconstruct voxels
            print "Loading generated texture arrays"
            frontfaceTex = TexturePool.load2dTextureArray(
                "temp/" + dirName + "_frontface_#####.png")
            backfaceTex = TexturePool.load2dTextureArray(
                "temp/" + dirName + "_backface_#####.png")

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
                (gridResolution/16, gridResolution/16, 1), sattr, self.win.get_gsg())

            # Save result texture
            self.graphicsEngine.extract_texture_data(
                    storage, self.win.getGsg())
            self.directionTextures[dirName] = storage
            storage.write(join(destination, "result_" + dirName + ".png"))

        # finally, combine all textures
        resultTexture = Texture("result")
        resultTexture.setup2dTexture(
                gridResolution * gridResolution, gridResolution,
                Texture.TFloat, Texture.FRgba16)

        self.combineNode.setShaderInput("directionX", self.directionTextures["x"])
        self.combineNode.setShaderInput("directionY", self.directionTextures["y"])
        self.combineNode.setShaderInput("directionZ", self.directionTextures["z"])
        self.combineNode.setShaderInput("destination", resultTexture)
        self.combineNode.setShaderInput("gridSize", gridResolution)
        sattr = self.combineNode.get_attrib(ShaderAttrib)
        self.graphicsEngine.dispatch_compute(
                ( gridResolution/8, gridResolution/8, gridResolution/8), sattr, self.win.get_gsg())
        self.graphicsEngine.extract_texture_data(
                resultTexture, self.win.getGsg())

        resultTexture.write(join(destination, "result_combined.png"))


        self.graphicsEngine.removeWindow(self.layerBuffer)
        self.layerScene.removeNode()
        self.layerCamera.removeNode()


        # Remove temp path
        if isdir("temp"):
            shutil.rmtree("temp")
            time.sleep(0.1)


        print "Done!"

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
        voxelizer.voxelize(f, d, dest)
