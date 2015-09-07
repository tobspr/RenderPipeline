
import struct

from panda3d.core import PTAInt, PTAFloat, Texture, Shader

from ..Util.DebugObject import DebugObject
from ..Util.Image import Image
from ..Util.FunctionDecorators import protected
from ..Util.RenderTarget import RenderTarget
from GPUCommand import GPUCommand

class GPUCommandQueue(DebugObject):

    """ This class offers an interface to the gpu, allowing commands to be
    pushed to a queue which then get executed on the gpu """

    def __init__(self, pipeline):
        DebugObject.__init__(self, "GPUCommandQueue")
        self.pipeline = pipeline
        self.commandsPerFrame = 1
        self.ptaNumCommands = PTAInt.emptyArray(1)
        self._createDataStorage()
        self._createCommandTarget()

        self.commands = []

    def clearQueue(self):
        """ Clears all commands currently being in the queue """
        pass

    def processQueue(self):
        """ Processes the n first commands of the queue """

        self.dataTexture.clearImage()
        commands = self.commands[:self.commandsPerFrame]
        self.commands = self.commands[self.commandsPerFrame:]
        self.ptaNumCommands[0] = len(commands)
        data = []
        for command in commands:
            # self.debug("Processing command", command)
            data += command.getData()



        if len(data) > 0:
            # self.debug("Processed", self.ptaNumCommands[0], "commands")
            # Pack the data into the buffer
            image = memoryview(self.dataTexture.tex.modifyRamImage())
            dataByteSize = len(data) * 4
            image[dataByteSize:] = "\0" * (len(image) - dataByteSize)
            image[0:dataByteSize] = struct.pack('f' * len(data), *data)

    def addCommand(self, command):
        """ Adds a new command """
        assert isinstance(command, GPUCommand)
        # self.debug("Adding command", command,"with size", command.getDataSize())
        self.commands.append(command)

    def reloadShaders(self):
        """ Reloads the command shader """
        commandShader = Shader.load(Shader.SLGLSL, "Shader/DefaultPostProcess.vertex", "Shader/ProcessCommandQueue.fragment")
        self.commandTarget.setShader(commandShader)

    def registerInput(self, key, val):
        """ Registers an new shader input to the command target """
        self.commandTarget.setShaderInput(key, val)

    @protected
    def _createDataStorage(self):
        """ Creates the buffer used to transfer commands """
        commandBufferSize = self.commandsPerFrame * 32
        self.debug("Allocating command buffer of size", commandBufferSize)
        self.dataTexture = Image.createBuffer("CommandQueue", commandBufferSize, Texture.TFloat, Texture.FR32)
        self.dataTexture.setClearColor(0)

    @protected
    def _createCommandTarget(self):
        """ Creates the target which processes the commands """
        self.commandTarget = RenderTarget("CommandTarget")
        self.commandTarget.addColorTexture()
        self.commandTarget.setSize(1, 1)
        self.commandTarget.prepareOffscreenBuffer()
        self.commandTarget.setShaderInput("CommandQueue", self.dataTexture.tex)
        self.commandTarget.setShaderInput("commandCount", self.ptaNumCommands)
