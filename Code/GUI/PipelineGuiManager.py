
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
        self.setup()

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


        register_feature("Blur GI/Occl.", "ft_UPSCALE_BLUR")

        register_mode("Lighting", "rm_Lighting")
        register_mode("Raw-Lighting", "rm_Diffuse_Lighting")

        if s.enableScattering:
            register_mode("Scattering", "rm_Scattering")
            register_feature("Scattering", "ft_SCATTERING")

        if s.enableGlobalIllumination:
            register_mode("G-Illum", "rm_GI")
            register_mode("GI-Reflections", "rm_Reflections")
            register_feature("G-Illum", "ft_GI")

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
            register_mode("Shadowing", "rm_SHADOWS")
            
            if s.usePCSS:
                register_feature("PCSS", "ft_PCSS")

            register_feature("PCF", "ft_PCF")

        register_feature("Env. Filtering", "ft_FILTER_ENVIRONMENT")
        register_feature("PBS", "ft_COMPLEX_LIGHTING")

        # register_mode("h Debug", "rm_SSaLR")

        if s.enableSSLR:
            register_feature("SSLR", "ft_SSLR")


        if s.useTransparency:
            register_feature("Transparency", "ft_TRANSPARENCY")

        # register_mode("Shadow Load", "rm_SHADOW_COMPUTATIONS")
        # register_mode("Lights Load", "rm_LIGHT_COMPUTATIONS")

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
            x=20, y=currentY+20, size=230, parent=self.debuggerContent)

        self.demoText = BetterOnscreenText(x=20, y=currentY,
                                       text="Sun Position", align="left", parent=self.debuggerContent,
                                       size=15, color=Vec3(1.0))

        currentY += 70


        if s.enableGlobalIllumination:

            self.slider_opts = {
                "ao_cone_height": {
                    "name": "AO Cone Height",
                    "min": 0.0001,
                    "max": 4.0,
                    "default": 0.5,
                },
                "ao_step_ratio": {
                    "name": "AO Step Ratio",
                    "min": 1.0,
                    "max": 2.5,
                    "default": 1.1,
                },
                "ao_cone_ratio": {
                    "name": "AO Cone Ratio",
                    "min": 0.00001,
                    "max": 2.5,
                    "default": 1.1,
                },
                "ao_start_distance": {
                    "name": "AO Start Offset",
                    "min": -2.0,
                    "max": 2.0,
                    "default": 0.5,
                },
                "ao_initial_radius": {
                    "name": "AO Initial Cone Radius",
                    "min": 0.0001,
                    "max": 5.0,
                    "default": 1.2,
                },

            }

           

            for name, opts in self.slider_opts.items():
                opts["slider"] = BetterSlider(
                    x=20, y=currentY+20, size=230, minValue=opts["min"],maxValue=opts["max"], value=opts["default"], parent=self.debuggerContent, callback=self._optsChanged)

                opts["label"] = BetterOnscreenText(x=20, y=currentY,
                                               text=opts["name"], align="left", parent=self.debuggerContent,
                                               size=15, color=Vec3(1.0))

                opts["value_label"] = BetterOnscreenText(x=250, y=currentY,
                                               text=str(opts["default"]), align="right", parent=self.debuggerContent,
                                               size=15, color=Vec3(0.6),mayChange=True)
                currentY += 50

        self.initialized = True
            
    def onPipelineLoaded(self):

        if self.pipeline.settings.enableGlobalIllumination:
            self._optsChanged()

    def _optsChanged(self):
        return
        container = self.pipeline.giPrecomputeBuffer

        for name, opt in self.slider_opts.items():
            container.setShaderInput("opt_" + name, opt["slider"].getValue())
            opt["value_label"].setText("{:0.4f}".format(opt["slider"].getValue()))
        

    def _updateSetting(self, status, name, updateWhenFalse=False):
        # Render Modes

        if hasattr(self.pipeline, "renderPassManager"):

            define = lambda key, val: self.pipeline.getRenderPassManager().registerDefine(key, val)
            undefine = lambda key: self.pipeline.getRenderPassManager().unregisterDefine(key)

            if name.startswith("rm_"):
                modeId = "DEBUG_RM_" + name[3:].upper()

                if status:
                    define(modeId, 1)
                else:
                    undefine(modeId)

                if name == "rm_Default":
                    undefine("DEBUG_VISUALIZATION_ACTIVE")
                else:
                    define("DEBUG_VISUALIZATION_ACTIVE", 1)

            elif name.startswith("ft_"):
                # instead of enabling per feature, we disable per feature
                modeId = "DEBUG_DISABLE_" + name[3:].upper()

                if status:
                    undefine(modeId)
                else:
                    define(modeId, 1)

            if self.initialized and (status is True or updateWhenFalse):
                self.pipeline.reloadShaders()
                # pass

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

            # self.watermark.hide()
            # self.showDebugger.hide()

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
