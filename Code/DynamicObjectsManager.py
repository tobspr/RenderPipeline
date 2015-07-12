
from panda3d.core import Texture, GeomEnums, InternalName, GeomVertexArrayFormat
from panda3d.core import GeomVertexFormat, Vec4, GeomVertexWriter, GeomVertexReader
from panda3d.core import Shader

from DebugObject import DebugObject
from MemoryMonitor import MemoryMonitor
from Globals import Globals

class DynamicObjectsManager(DebugObject):

    """ The dynamic objects manager stores a buffer for each vertex and tracks
    its current position aswell as the last frame position. This ensures correct
    velocity for animated and moving objects. """

    def __init__(self, pipeline):
        """ Creates the manager and creates the vertex buffer"""
        DebugObject.__init__(self, "DynamicObjectsManager")
        self.pipeline = pipeline
        self.currentIndex = 0
        self.maxVertexCount = 1000000
        self.init()

    def init(self):
        """ Initializes the vertex buffers and makes them available as shader
        inputs. """

        self.vertexBuffer = Texture("VertexPositionBuffer")
        self.vertexBuffer.setupBufferTexture(self.maxVertexCount, Texture.TFloat, 
            Texture.FRgba32, GeomEnums.UH_static)
        self.vertexBuffer.setClearColor(Vec4(0))
        self.vertexBuffer.clearImage()

        MemoryMonitor.addTexture("DynamicObjectVtxBuffer", self.vertexBuffer)

        Globals.render.setShaderInput("DynamicObjectVtxBuffer", self.vertexBuffer)

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

        # Assign the standard animated shader
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultShaders/Opaque/vertex_dynamic.glsl",
            "Shader/DefaultShaders/Opaque/fragment.glsl")
        obj.setShader(shader, 25)

    def unregisterObject(self, obj):
        """ Unregisters a dynamic object which was registered with registerObject.
        This frees up the space used by the object and should be called whenever
        the object is not used anymore """
        # TODO
        pass