
from panda3d.core import Texture, ShaderAttrib, NodePath, Vec4

from DebugObject import DebugObject
from BetterShader import BetterShader
from Globals import Globals
from TextureCleaner import TextureCleaner


class TextureDebugger(DebugObject):

    """ Tool to write Textures to disk """

    def __init__(self):
        """ Creates a new texture debugger """
        DebugObject.__init__(self, "TextureDebugger")

    def debug3DTexture(self, tex, dest):

        """ Writes a 3D Texture to disk """

        effectiveHeight = (tex.getYSize()+1) * (tex.getZSize())
        effectiveHeight -= 1
        effectiveWidth = (tex.getXSize()+1)*3

        effectiveHeight = tex.getYSize()
        effectiveWidth = tex.getXSize()

        
        self.debug("Texture Size =",tex.getXSize(),"x",tex.getYSize(),"x",tex.getZSize())
        self.debug("EffectiveHeight = ", effectiveHeight, "Layers=",tex.getZSize())
        
        store = Texture("store")
        store.setup2dTexture(
            effectiveWidth, effectiveHeight, Texture.TFloat, Texture.FRgba16)

        TextureCleaner.clearTexture(store, Vec4(1,0,1,1))

        # Create a dummy node and apply the shader to it
        shader = BetterShader.loadCompute("Shader/Write3DTexture.compute")
        dummy = NodePath("dummy")
        dummy.setShader(shader)
        dummy.setShaderInput("source", tex)
        dummy.setShaderInput("height", tex.getYSize() + 1)
        dummy.setShaderInput("width", tex.getXSize() + 1)
        dummy.setShaderInput("layerCount", tex.getZSize())
        dummy.setShaderInput("destination", store)

        # Retrieve the underlying ShaderAttrib
        sattr = dummy.get_attrib(ShaderAttrib)

        # Dispatch the compute shader, right now!
        Globals.base.graphicsEngine.dispatch_compute(
            (tex.getXSize() / 16, tex.getYSize() / 16, tex.getZSize()), sattr, base.win.get_gsg())

        Globals.base.graphicsEngine.extract_texture_data(
                store, Globals.base.win.getGsg())


        store.write(dest)
