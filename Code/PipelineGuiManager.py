
import math
from direct.stdpy.file import join

from panda3d.core import TransparencyAttrib, Texture, Vec3
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectCheckBox import DirectCheckBox
import direct.gui.DirectGuiGlobals as DGG
from direct.interval.IntervalGlobal import Sequence, Parallel

from Globals import Globals
from DebugObject import DebugObject


class BetterOnscreenImage(DebugObject):

    def __init__(self, image=None, parent=None, x=0, y=0, w=10, h=10, transparent=True, nearFilter=True):
        DebugObject.__init__(self, "BOnscreenImage")

        self.initialPos = Vec3(x + w / 2.0, 1, -y - h / 2.0)

        self._node = OnscreenImage(
            image=image, parent=parent, pos=self.initialPos, scale=(w / 2.0,  1, h / 2.0))

        if transparent:
            self._node.setTransparency(TransparencyAttrib.MAlpha)

        tex = self._node.getTexture()
        tex.setMinfilter(Texture.FTNearest)
        tex.setMagfilter(Texture.FTNearest)
        tex.setAnisotropicDegree(8)
        tex.setWrapU(Texture.WMClamp)
        tex.setWrapV(Texture.WMClamp)

    def getInitialPos(self):
        return self.initialPos

    def posInterval(self, *args, **kwargs):
        return self._node.posInterval(*args, **kwargs)


class BetterCheckbox(DebugObject):

    def __init__(self, parent=None, x=0, y=0, callback=None, extraArgs=None, radio=False, expandW=100, checked=False):
        DebugObject.__init__(self, "BCheckbox")

        prefix = "Checkbox" if not radio else "Radiobox"

        checkedImg = Globals.loader.loadTexture("Data/GUI/" + prefix + "Active.png")
        uncheckedImg = Globals.loader.loadTexture("Data/GUI/" + prefix + "Empty.png")

        for tex in [checkedImg, uncheckedImg]:
            tex.setMinfilter(Texture.FTNearest)
            tex.setMagfilter(Texture.FTNearest)
            tex.setAnisotropicDegree(0)
            tex.setWrapU(Texture.WMClamp)
            tex.setWrapV(Texture.WMClamp)

        self._node = DirectCheckBox(parent=parent, pos=(
            x + 7.5, 1, -y - 7.5), scale=(15 / 2.0, 1, 15 / 2.0), checkedImage=checkedImg, uncheckedImage=uncheckedImg,
            image=uncheckedImg, extraArgs = extraArgs, state=DGG.NORMAL,
            relief=DGG.FLAT, command=self._updateStatus)

        self._node["frameColor"] = (0, 0, 0, 0.0)
        self._node["frameSize"] = (-2, 2 + expandW / 7.5, -1.6, 1.6)

        self._node.setTransparency(TransparencyAttrib.MAlpha)

        self.callback = callback
        self.extraArgs = extraArgs
        self.collection = None

        if checked:
            self._setChecked(True)

    def _setCollection(self, coll):
        self.collection = coll

    def _updateStatus(self, status, *args):
        if self.collection:
            if status:
                self.collection._changed(self)
                # A radio box can't be unchecked
                self._node["state"] = DGG.DISABLED

        if self.callback is not None:
            self.callback(*([status] + self.extraArgs))

    def _setChecked(self, val):
        self._node["isChecked"] = val

        if val:
            self._node['image'] = self._node['checkedImage']
        else:
            self._node['image'] = self._node['uncheckedImage']

        if self.callback is not None:
            self.callback(*([val] + self.extraArgs))


class CheckboxCollection(DebugObject):

    def __init__(self):
        DebugObject.__init__(self, "CheckboxCollection")
        self.items = []

    def add(self, chb):
        if chb.collection is not None:
            self.error(
                "Can't add checkbox as it already belongs to another collection")
            return

        chb._setCollection(self)
        self.items.append(chb)

    def _changed(self, chb):
        for item in self.items:
            if item is not chb:
                item._setChecked(False)
                item._node["state"] = DGG.NORMAL


class PipelineGuiManager(DebugObject):

    """ This class manages the onscreen debug gui for
    the pipeline """

    def __init__(self, pipeline):
        DebugObject.__init__(self, "GUIManager")
        self.pipeline = pipeline
        self.body = Globals.base.pixel2d
        self.showbase = pipeline.showbase
        self.guiActive = False

        self.defines = {}

    def update(self):
        pass

    def setup(self):
        """ Setups this manager """

        self.debug("Creating GUI ..")

        self.initialized = False
        self.rootNode = self.body.attachNewNode("GUIManager")
        self.rootNode.setPos(0, 1, 0)

        self.watermark = BetterOnscreenImage(
            image="Data/GUI/Watermark.png", parent=self.rootNode, x=20, y=20, w=230, h=55)
        self.showDebugger = BetterOnscreenImage(
            image="Data/GUI/ShowDebugger.png", parent=self.rootNode, x=20, y=80, w=230, h=36)
        self.debuggerParent = self.rootNode.attachNewNode("DebuggerParent")
        self.debuggerParent.setPos(-350, 0, 0)
        self.debuggerBackground = BetterOnscreenImage(
            image="Data/GUI/DebuggerBackground.png", parent=self.debuggerParent, x=0, y=0, w=279, h=1200)

        self._initSettings()

        self.showbase.accept("g", self._toggleGUI)

        self.currentGUIEffect = None



        # self._toggleGUI()

    def _initSettings(self):
        currY = 83

        # Render Modes
        self.renderModes = CheckboxCollection()

        checkboxX = 20

        self.chbRM_Default = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX, y=currY, callback=self._updateSetting, extraArgs=["rm_Default", False], radio=True)
        self.chbRM_Metallic = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX + 138, y=currY, callback=self._updateSetting, extraArgs=["rm_Metallic", False], radio=True)

        currY += 25

        self.chbRM_BaseColor = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX, y=currY, callback=self._updateSetting, extraArgs=["rm_BaseColor", False], radio=True)
        self.chbRM_Roughness = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX + 138, y=currY, callback=self._updateSetting, extraArgs=["rm_Roughness", False], radio=True)

        currY += 25

        self.chbRM_Specular = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX, y=currY, callback=self._updateSetting, extraArgs=["rm_Specular", False], radio=True)
        self.chbRM_Normal = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX + 138, y=currY, callback=self._updateSetting, extraArgs=["rm_Normal", False], radio=True)

        currY += 25

        self.chbRM_SSDO = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX, y=currY, callback=self._updateSetting, extraArgs=["rm_SSDO", False], radio=True)

        self.chbRM_Lighting = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX + 138, y=currY, callback=self._updateSetting, extraArgs=["rm_Lighting", False], radio=True)


        currY += 25

        self.chbRM_Scattering = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX, y=currY, callback=self._updateSetting, extraArgs=["rm_SCATTERING", False], radio=True)


        # self.chbRM_Wireframe = BetterCheckbox(
        # parent=self.debuggerParent, x=150, y=currY,
        # callback=self._updateSetting, extraArgs=["rm_Wireframe", False],
        # radio=True)

        self.chbRM_Default._setChecked(True)

        self.renderModes.add(self.chbRM_Default)
        self.renderModes.add(self.chbRM_Metallic)
        self.renderModes.add(self.chbRM_BaseColor)
        self.renderModes.add(self.chbRM_Roughness)
        self.renderModes.add(self.chbRM_Specular)
        self.renderModes.add(self.chbRM_Normal)
        self.renderModes.add(self.chbRM_SSDO)
        self.renderModes.add(self.chbRM_Lighting)
        self.renderModes.add(self.chbRM_Scattering)

        # Features

        currY = 250

        self.chbFT_SSDO = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX, y=currY, callback=self._updateSetting, extraArgs=["ft_SSDO", True], checked=True)

        self.chbFT_MotionBlur = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX + 138, y=currY, callback=self._updateSetting, extraArgs=["ft_MOTIONBLUR", True], checked=True)

        currY += 25

        self.chbFT_AA = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX, y=currY, callback=self._updateSetting, extraArgs=["ft_ANTIALIASING", True], checked=True)

        self.chbFT_Shadows = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX + 138, y=currY, callback=self._updateSetting, extraArgs=["ft_SHADOWS", True], checked=True)

        currY += 25

        self.chbFT_ColorCorrect = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX, y=currY, callback=self._updateSetting, extraArgs=["ft_COLOR_CORRECTION", True], checked=True)


        self.chbFT_AOBlur = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX + 138, y=currY, callback=self._updateSetting, extraArgs=["ft_BLUR_OCCLUSION", True], checked=True)


        currY += 25

        self.chbFT_Scattering = BetterCheckbox(
            parent=self.debuggerParent, x=checkboxX, y=currY, callback=self._updateSetting, extraArgs=["ft_SCATTERING", True], checked=True)



        self.initialized = True



    def _updateSetting(self, status, name, updateWhenFalse=False):
        # self.debug("Update setting:", name, "=", status, "whenFalse=",updateWhenFalse)

        # Render Modes
        if name.startswith("rm_"):
            modeId = "RM_" + name[3:].upper()
            self.defines[modeId] = 1 if status else 0

        elif name.startswith("ft_"):
            # instead of enabling per feature, we disable per feature
            modeId = "DISABLE_" + name[3:].upper()
            self.defines[modeId] = 0 if status else 1


        if self.initialized and (status is True or updateWhenFalse):
            self.pipeline._generateShaderConfiguration()
            self.pipeline.reloadShaders()

    def getDefines(self):
        result = []

        for key, val in self.defines.items():
            # print key, val
            if val:
                result.append(("DEBUG_" + key, val))

        # print result
        return result

    def _toggleGUI(self):
        self.debug("Toggle overlay")

        if self.currentGUIEffect is not None:
            self.currentGUIEffect.finish()

        if not self.guiActive:
            self.currentGUIEffect = Parallel(
                self.watermark.posInterval(
                    0.4, self.watermark.getInitialPos() + Vec3(0, 0, 200), blendType="easeIn"),
                self.showDebugger.posInterval(
                    0.4, self.showDebugger.getInitialPos() + Vec3(0, 0, 400), blendType="easeIn"),
                self.debuggerParent.posInterval(
                    0.3, Vec3(0, 0, 0), blendType="easeOut"),
            )
            self.currentGUIEffect.start()

        else:
            self.currentGUIEffect = Parallel(
                self.watermark.posInterval(
                    0.4, self.watermark.getInitialPos(), blendType="easeOut"),
                self.showDebugger.posInterval(
                    0.4, self.showDebugger.getInitialPos(), blendType="easeOut"),
                self.debuggerParent.posInterval(
                    0.3, Vec3(-350, 0, 0), blendType="easeInOut"),
            )
            self.currentGUIEffect.start()

        self.guiActive = not self.guiActive
