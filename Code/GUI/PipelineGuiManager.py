
from panda3d.core import Vec3
from direct.interval.IntervalGlobal import Parallel, Sequence, Wait

from ..Globals import Globals
from ..DebugObject import DebugObject
from BufferViewerGUI import BufferViewerGUI
from BetterOnscreenImage import BetterOnscreenImage
from BetterSlider import BetterSlider
from BetterOnscreenText import BetterOnscreenText
from CheckboxWithLabel import CheckboxWithLabel
from CheckboxCollection import CheckboxCollection
from UIWindow import UIWindow


class PipelineGuiManager(DebugObject):

    """ This class manages the onscreen debug gui for
    the pipeline """

    def __init__(self, pipeline):
        DebugObject.__init__(self, "GUIManager")
        self.pipeline = pipeline
        self.body = Globals.base.pixel2d
        self.showbase = pipeline.showbase
        self.guiActive = False
        self.window = UIWindow(
            "Pipeline Debugger", 280, Globals.base.win.getYSize())
        self.defines = {}
        self.bufferViewerParent = Globals.base.pixel2d.attachNewNode(
            "Buffer Viewer GUI")
        self.bufferViewer = BufferViewerGUI(self.bufferViewerParent)

    def update(self):
        pass

    def setup(self):
        """ Setups this manager """
        self.debug("Creating GUI ..")
        self.initialized = False
        self.rootNode = self.body.attachNewNode("GUIManager")
        self.rootNode.setPos(0, 1, 0)
        self.watermark = BetterOnscreenImage(
            image="Data/GUI/Watermark.png", parent=self.rootNode,
            x=20, y=20, w=230, h=55)
        self.showDebugger = BetterOnscreenImage(
            image="Data/GUI/ShowDebugger.png", parent=self.rootNode,
            x=20, y=80, w=230, h=36)
        self.debuggerParent = self.window.getNode()
        self.debuggerParent.setPos(-350, 0, 0)
        self.debuggerContent = self.window.getContentNode()
        self._initSettings()
        self.showbase.accept("g", self._toggleGUI)
        self.currentGUIEffect = None

        # self._toggleGUI()
    def _initSettings(self):
        currentY = 10

        # Render Modes
        self.renderModes = CheckboxCollection()

        # Handle to the settings
        s = self.pipeline.settings

        modes = []
        features = []

        register_mode = lambda name, mid: modes.append((name, mid))
        register_feature = lambda name, fid: features.append((name, fid))

        register_mode("Default", "rm_Default")
        register_mode("Metallic", "rm_Metallic")
        register_mode("BaseColor", "rm_BaseColor")
        register_mode("Roughness", "rm_Roughness")
        register_mode("Specular", "rm_Specular")
        register_mode("Normal", "rm_Normal")

        if s.occlusionTechnique != "None":
            register_mode("Occlusion", "rm_Occlusion")
            register_feature("Occlusion", "ft_OCCLUSION")
            register_feature("Blur Occlusion", "ft_BLUR_OCCLUSION")

        register_mode("Lighting", "rm_Lighting")

        if s.enableScattering:
            register_mode("Scattering", "rm_Scattering")
            register_feature("Scattering", "ft_SCATTERING")

        if s.enableGlobalIllumination:
            register_mode("G-Illum", "rm_GI")
            register_mode("GI-Reflections", "rm_Reflections")
            register_feature("G-Illum", "ft_GI")

            register_feature("Update GI", "update_gi")


        register_mode("Ambient", "rm_Ambient")
        register_feature("Ambient", "ft_AMBIENT")

        if s.motionBlurEnabled:
            register_feature("Motion Blur", "ft_MOTIONBLUR")

        if s.antialiasingTechnique != "None":
            register_feature("Anti-Aliasing", "ft_ANTIALIASING")

        register_feature("Shadows", "ft_SHADOWS")
        register_feature("Color Correction", "ft_COLOR_CORRECTION")
        
        if s.renderShadows:
            register_mode("PSSM Splits", "rm_PSSM_SPLITS")
            register_feature("PCSS", "ft_PCSS")

        self.renderModesTitle = BetterOnscreenText(text="Render Mode",
                                                   x=20, y=currentY,
                                                   parent=self.debuggerContent,
                                                   color=Vec3(1), size=15)

        currentY += 80
        isLeft = True
        for modeName, modeID in modes:

            box = CheckboxWithLabel(
                parent=self.debuggerParent, x=20 if isLeft else 158, y=currentY,
                chbCallback=self._updateSetting, chbArgs=[modeID, False],
                radio=True, textSize=14, text=modeName, textColor=Vec3(0.6),
                chbChecked=modeID == "rm_Default")
            self.renderModes.add(box.getCheckbox())

            isLeft = not isLeft

            if isLeft:
                currentY += 25

        self.featuresTitle = BetterOnscreenText(text="Toggle Features",
                                                x=20, y=currentY, parent=self.debuggerContent, color=Vec3(1), size=15)

        currentY += 80
        isLeft = True
        for featureName, featureID in features:

            box = CheckboxWithLabel(
                parent=self.debuggerParent, x=20 if isLeft else 158, y=currentY,
                chbCallback=self._updateSetting, chbArgs=[featureID, True],
                textSize=14, text=featureName, textColor=Vec3(0.6),
                chbChecked=True)

            isLeft = not isLeft

            if isLeft:
                currentY += 25

        self.demoSlider = BetterSlider(
            x=20, y=currentY, size=230, parent=self.debuggerContent)

        self.initialized = True

    def _updateSetting(self, status, name, updateWhenFalse=False):
        # Render Modes
        if name.startswith("rm_"):
            modeId = "RM_" + name[3:].upper()
            self.defines[modeId] = 1 if status else 0

        elif name.startswith("ft_"):
            # instead of enabling per feature, we disable per feature
            modeId = "DISABLE_" + name[3:].upper()
            self.defines[modeId] = 0 if status else 1

        elif name == "update_gi":
            self.pipeline.globalIllum.setUpdateEnabled(status)


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
            # show debugger
            self.currentGUIEffect = Parallel(
                self.watermark.posInterval(
                    0.4, self.watermark.getInitialPos() + Vec3(0, 0, 200),
                    blendType="easeIn"),
                self.showDebugger.posInterval(
                    0.4, self.showDebugger.getInitialPos() + Vec3(0, 0, 400),
                    blendType="easeIn"),
                self.debuggerParent.posInterval(
                    0.3, Vec3(0, 0, 0), blendType="easeOut"),
                Sequence(
                    Wait(0.2),
                    self.bufferViewerParent.posInterval(
                        0.11, Vec3(30, 0, 0), blendType="easeOut")
                )
            )
            self.currentGUIEffect.start()

            self.watermark.hide()
            self.showDebugger.hide()

        else:
            # hide debugger
            self.currentGUIEffect = Parallel(
                self.watermark.posInterval(
                    0.4, self.watermark.getInitialPos(), blendType="easeOut"),
                self.showDebugger.posInterval(
                    0.4, self.showDebugger.getInitialPos(),
                    blendType="easeOut"),
                self.debuggerParent.posInterval(
                    0.3, Vec3(-350, 0, 0), blendType="easeInOut"),
                self.bufferViewerParent.posInterval(
                    0.15, Vec3(0, 0, 0), blendType="easeOut")
            )
            self.currentGUIEffect.start()

        self.guiActive = not self.guiActive
