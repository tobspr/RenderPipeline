
from panda3d.core import Texture, GeomEnums, InternalName, GeomVertexArrayFormat
from panda3d.core import GeomVertexFormat, Vec4, GeomVertexWriter, GeomVertexReader
from panda3d.core import Shader

from DebugObject import DebugObject
from MemoryMonitor import MemoryMonitor
from Globals import Globals

from GUI.BufferViewerGUI import BufferViewerGUI

class DynamicObjectsManager(DebugObject):

    """ The dynamic objects manager stores a buffer for each vertex and tracks
    its current position aswell as the last frame position. This ensures correct
    velocity for animated and moving objects. """

    def __init__(self, pipeline):
        """ Creates the manager and creates the vertex buffer"""
        DebugObject.__init__(self, "DynamicObjectsManager")
        self.pipeline = pipeline
        self.currentIndex = 0
        self.maxVertexCount = 50000
        self.split = 500
        self.init()

    def init(self):
        """ Initializes the vertex buffers and makes them available as shader
        inputs. """

        self.vertexBuffers = []

        for i in xrange(2):
            vertexBuffer = Texture("VertexPositionBuffer-" + str(i))
            vertexBuffer.setup2dTexture(self.split, self.maxVertexCount / self.split, Texture.TFloat, Texture.FRgba32)
            vertexBuffer.setClearColor(Vec4(0))
            vertexBuffer.clearImage()

            MemoryMonitor.addTexture("DynamicObjectVtxBuffer"+str(i), vertexBuffer)
            Globals.render.setShaderInput("dynamicObjectVtxBuffer"+str(i), vertexBuffer)

            BufferViewerGUI.registerTexture("Vtx Positions " + str(i), vertexBuffer)
            vertexBuffer.setWrapU(Texture.WMClamp)
            vertexBuffer.setWrapV(Texture.WMClamp)
            vertexBuffer.setMinfilter(Texture.FTNearest)
            vertexBuffer.setMagfilter(Texture.FTNearest)
            self.vertexBuffers.append(vertexBuffer)

        Globals.render.setShaderInput("dynamicVtxSplit", self.split)

    def update(self):
        """ Update method, currently not used """
        pass

    def registerObject(self, obj):
        """ Registers a new dynamic object, this will store an index for every
        vertex, which can be used to read and store last position data in order
        to compute the velocity. This method also assigns the standard animated
        shader to the node """

        self.debug("Registering dynamic object")

        # Find all GeomNodes
        for node in obj.findAllMatches("**/+GeomNode"):
            geomNode = node.node()
            geomCount = geomNode.getNumGeoms()

            # Find all Geoms
            for i in xrange(geomCount):

                # Modify vertex data
                geom = geomNode.modifyGeom(i)
                geomVertexData = geom.modifyVertexData()

                # Add a new column named "dovindex" to the vertex data
                formatArray = GeomVertexArrayFormat() 
                formatArray.addColumn(InternalName.make("dovindex"), 1, GeomEnums.NTUint32, GeomEnums.CIndex) 
                newArrayFormat = GeomVertexFormat(geomVertexData.getFormat())
                newArrayFormat.addArray(formatArray)
                newArrayFormat = GeomVertexFormat.registerFormat(newArrayFormat)

                # Convert the old vertex data and assign the new vertex data
                convertedVertexData = geomVertexData.convertTo(newArrayFormat)
                geom.setVertexData(convertedVertexData)

                # Write the per-vertex indices the dovindex column 
                newVertexData = geom.modifyVertexData()
                vtxReader = GeomVertexReader(newVertexData, "vertex")
                indexWriter = GeomVertexWriter(newVertexData, "dovindex")

                while not vtxReader.isAtEnd():
                    data = vtxReader.getData3f()
                    indexWriter.setData1i(self.currentIndex)
                    self.currentIndex += 1

    def unregisterObject(self, obj):
        """ Unregisters a dynamic object which was registered with registerObject.
        This frees up the space used by the object and should be called whenever
        the object is not used anymore """
        # TODO
        pass