
from panda3d.core import * 

from Code.DebugObject import DebugObject
from Code.GUI.BetterOnscreenImage import BetterOnscreenImage

import direct.gui.DirectGuiGlobals as DGG

from EditorCategory import EditorCategories

from direct.gui.DirectFrame import DirectFrame
from functools import partial


class EditorGUI(DebugObject):

    def __init__(self):
        DebugObject.__init__(self, "EditorGUI")
        self.parent = base.pixel2d
        self._createComponents()

    def _createComponents(self):
        self.debug("Creating GUI Components")

        self.categoryMenu = self.parent.attachNewNode("CategoryMenu")
        self.categoryMenu.setPos(-350, 0, -49)

        self.sidebar = self.parent.attachNewNode("EditorSidebar")

        self.sidebarBackground = DirectFrame(parent=self.sidebar, pos=(0, 0, 0), frameSize=(
            0, 92, 0, -base.win.getYSize()), frameColor=(0.05, 0.05, 0.05, 1.0))

        self.logo = BetterOnscreenImage(parent=self.sidebar, transparent=False,
                                        image="Editor/GUI/logo.png", x=0, y=0, w=92, h=48)


        self.categoriesParent = self.sidebar.attachNewNode("Categories")
        self.categoriesParent.setPos(0, 0, -48)


        
        self.categoryIcons = {}

        self.animations = {
            "moveMenuArrow": None,
            "moveCategoryMenu": None
        }

        for index, category in enumerate(EditorCategories.Categories):
            iconDefault = "Editor/GUI/Icon-" + category.name + ".png"
            iconHover = "Editor/GUI/Icon-" + category.name + "-Hover.png"
            # iconActive = "Editor/GUI/Icon-" + category.name + "-Hover.png"
            self.categoryIcons[category.name] = BetterOnscreenImage(parent=self.categoriesParent, transparent=False,
                                                                    image=iconDefault, x=0, y=94 * index, w=92, h=94)

            # i hate direct gui
            hoverCatch = DirectFrame(parent=self.categoriesParent,
                                     frameSize=(0, 92, 0, -94), pos=(0, 0, -94 * index),
                                     frameColor=(0, 0, 0, 0), state=DGG.NORMAL)

            # Add a hover effect
            hoverCatch.bind(
                DGG.ENTER, partial(self._showCategoryMenu, category.name))
            hoverCatch.bind(
                DGG.EXIT, partial(self._hideCategoryMenu, category.name))

        self.currentCategoryMarker = BetterOnscreenImage(parent=self.categoriesParent,
                                                         image="Editor/GUI/Arrow-Right.png", x=92, y=0, w=11, h=21)

        self.currentCategoryMarker.hide()



        self.categoryMenuBg = DirectFrame(parent=self.categoryMenu, pos=(15,0,0), frameSize=(
                0, 300, 0, -400), frameColor=(0.2,0.2,0.2,1.0))
        # self.categoryMenuBg.hide()

    def _clearAnimation(self, name, finish=True):
        if self.animations[name] is not None:
            if finish:
                self.animations[name].finish()
            else:
                self.animations[name].clearToInitial()

    def _showCategoryMenu(self, name, coords):
        self.categoryIcons[name].setImage(
            "Editor/GUI/Icon-" + name + "-Hover.png")
        y = -self.categoryIcons[name]._node.getZ(self.categoriesParent)
        # self.currentCategoryMarker.setPos(92, y)
        # self.categoryMenuBg.show()
        self.currentCategoryMarker.show()
        self._clearAnimation("moveMenuArrow")
        self.animations["moveMenuArrow"] = self.currentCategoryMarker.posInterval(
                0.16, self.currentCategoryMarker.translatePos(92, y - 11), blendType="easeInOut")

        self.animations["moveMenuArrow"].start()

        self._clearAnimation("moveCategoryMenu", False)
        # self.categoryMenu.setZ(-y-1)
        self.animations["moveCategoryMenu"] = self.categoryMenu.posInterval(
                0.2, Vec3(92, 0, -y-1), blendType="easeOut")
        self.animations["moveCategoryMenu"].start()


    def _hideCategoryMenu(self, name, coords):
        self._clearAnimation("moveMenuArrow")
        self._clearAnimation("moveCategoryMenu")
        self.categoryIcons[name].setImage("Editor/GUI/Icon-" + name + ".png")
        self.currentCategoryMarker.hide()
        # self.categoryMenuBg.hide()

        self._clearAnimation("moveCategoryMenu", False)
        self.animations["moveCategoryMenu"] = self.categoryMenu.posInterval(
                0.2, Vec3(-350, 0, self.categoryMenu.getZ()), blendType="easeOut")
        self.animations["moveCategoryMenu"].start()