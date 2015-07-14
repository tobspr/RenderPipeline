# Author: Ryan Myers
# Models: Jeff Styers, Reagan Heller


# Last Updated: 6/13/2005
#
# This tutorial provides an example of creating a character
# and having it walk around on uneven terrain, as well
# as implementing a fully rotatable camera.


import sys
sys.path.insert(0, '../../')

# Now import the pipeline
from Code.RenderingPipeline import RenderingPipeline
from Code.DirectionalLight import DirectionalLight
from Code.Scattering import Scattering

from Code.GlobalIllumination import GlobalIllumination

from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import Filename, loadPrcFileData
from panda3d.core import PandaNode, NodePath, Camera, TextNode
from panda3d.core import Vec3, Vec4, BitMask32, loadPrcFile, Texture
from panda3d.core import Shader
from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
from direct.showbase.ShowBase import ShowBase
import random
import sys
import os
import math

SPEED = 0.5

# Function to put instructions on the screen.


def addInstructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1),
                        pos=(-1.3, pos), align=TextNode.ALeft, scale = .05)

# Function to put title on the screen.


def addTitle(text):
    return OnscreenText(text=text, style=1, fg=(1, 1, 1, 1),
                        pos=(1.3, -0.95), align=TextNode.ARight, scale = .07)


class World(ShowBase):

    def __init__(self):

        # Load the default configuration.prc. This is recommended, as it
        # contains some important panda options
        loadPrcFile("../../Config/configuration.prc")

        ShowBase.__init__(self)

        # Create a new pipeline instance
        self.renderPipeline = RenderingPipeline(self)

        # Set the base path for the pipeline. This is required as we are in
        # a subdirectory
        self.renderPipeline.getMountManager().setBasePath("../../")

        # Also set the write path
        self.renderPipeline.getMountManager().setWritePath("../../Temp/")

        # Load the default settings
        self.renderPipeline.loadSettings("../../Config/pipeline.ini")

        # Now create the pipeline
        self.renderPipeline.create()

        # Add a directional light
        dPos = Vec3(40, 40, 40)
        dirLight = DirectionalLight()
        dirLight.setPos(dPos * 1000000.0)
        dirLight.setShadowMapResolution(2048)
        dirLight.setCastsShadows(True)
        dirLight.setColor(6, 6, 6)
        self.renderPipeline.addLight(dirLight)
        self.renderPipeline.setGILightSource(dirLight)




        self.keyMap = {
            "left": 0, "right": 0, "forward": 0, "cam-left": 0, "cam-right": 0}
        base.win.setClearColor(Vec4(0, 0, 0, 1))

        # Post the instructions

        self.title = addTitle(
            "Panda3D Tutorial: Roaming Ralph (Walking on Uneven Terrain)")
        self.inst1 = addInstructions(0.95, "[ESC]: Quit")
        self.inst2 = addInstructions(0.90, "[Left Arrow]: Rotate Ralph Left")
        self.inst3 = addInstructions(0.85, "[Right Arrow]: Rotate Ralph Right")
        self.inst4 = addInstructions(0.80, "[Up Arrow]: Run Ralph Forward")
        self.inst6 = addInstructions(0.70, "[A]: Rotate Camera Left")
        self.inst7 = addInstructions(0.65, "[S]: Rotate Camera Right")

        # Set up the environment
        # This environment model contains collision meshes.  If you look
        # in the egg file, you will see the following:
        #
        #    <Collide> { Polyset keep descend }
        #
        # This tag causes the following mesh to be converted to a collision
        # mesh -- a mesh which is optimized for collision, not rendering.
        # It also keeps the original mesh, so there are now two copies ---
        # one optimized for rendering, one for collisions.

        self.environ = loader.loadModel("models/world")
        self.environ.reparentTo(render)
        self.environ.setPos(0, 0, 0)

        self.environ.find("**/wall").removeNode()

        # Create the main character, Ralph
        ralphStartPos = self.environ.find("**/start_point").getPos()
        self.ralph = Actor("models/ralph",
                           {"run": "models/ralph-run",
                            "walk": "models/ralph-walk"})
        self.ralph.reparentTo(render)
        self.ralph.setScale(.2)
        self.ralph.setPos(ralphStartPos)

        self.renderPipeline.setEffect(self.ralph, "Effects/Default/Default.effect", {
                "dynamic": True
            })

        # Create a floater object.  We use the "floater" as a temporary
        # variable in a variety of calculations.

        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)

        # Accept the control keys for movement and rotation

        self.accept("escape", sys.exit)
        self.accept("arrow_left", self.setKey, ["left", 1])
        self.accept("arrow_right", self.setKey, ["right", 1])
        self.accept("arrow_up", self.setKey, ["forward", 1])
        self.accept("a", self.setKey, ["cam-left", 1])
        self.accept("s", self.setKey, ["cam-right", 1])
        self.accept("arrow_left-up", self.setKey, ["left", 0])
        self.accept("arrow_right-up", self.setKey, ["right", 0])
        self.accept("arrow_up-up", self.setKey, ["forward", 0])
        self.accept("a-up", self.setKey, ["cam-left", 0])
        self.accept("s-up", self.setKey, ["cam-right", 0])

        # NOTICE: It is important that your update tasks have a lower priority
        # than -10000
        taskMgr.add(self.move, "moveTask", priority=-20000)

        self.accept("r", self.reloadShader)

        # Game state variables
        self.isMoving = False

        # Set up the camera

        base.disableMouse()
        base.camera.setPos(self.ralph.getX(), self.ralph.getY() + 10, 1.2)

        # We will detect the height of the terrain by creating a collision
        # ray and casting it downward toward the terrain.  One ray will
        # start above ralph's head, and the other will start above the camera.
        # A ray may hit the terrain, or it may hit a rock or a tree.  If it
        # hits the terrain, we can detect the height.  If it hits anything
        # else, we rule that the move is illegal.

        self.cTrav = CollisionTraverser()

        self.ralphGroundRay = CollisionRay()
        self.ralphGroundRay.setOrigin(0, 0, 1000)
        self.ralphGroundRay.setDirection(0, 0, -1)
        self.ralphGroundCol = CollisionNode('ralphRay')
        self.ralphGroundCol.addSolid(self.ralphGroundRay)
        self.ralphGroundCol.setFromCollideMask(BitMask32.bit(0))
        self.ralphGroundCol.setIntoCollideMask(BitMask32.allOff())
        self.ralphGroundColNp = self.ralph.attachNewNode(self.ralphGroundCol)
        self.ralphGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.ralphGroundColNp, self.ralphGroundHandler)

        self.camGroundRay = CollisionRay()
        self.camGroundRay.setOrigin(0, 0, 1000)
        self.camGroundRay.setDirection(0, 0, -1)
        self.camGroundCol = CollisionNode('camRay')
        self.camGroundCol.addSolid(self.camGroundRay)
        self.camGroundCol.setFromCollideMask(BitMask32.bit(0))
        self.camGroundCol.setIntoCollideMask(BitMask32.allOff())
        self.camGroundColNp = base.camera.attachNewNode(self.camGroundCol)
        self.camGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.camGroundColNp, self.camGroundHandler)

        # Uncomment this line to see the collision rays
        # self.ralphGroundColNp.show()
        # self.camGroundColNp.show()

        # Uncomment this line to show a visual representation of the
        # collisions occuring
        # self.cTrav.showCollisions(render)

        self.skybox = self.renderPipeline.getDefaultSkybox()
        self.skybox.reparentTo(render)

        self.prepareSRGB(render)
        self.reloadShader()
        self.renderPipeline.onSceneInitialized()
        
    def reloadShader(self):
        self.renderPipeline.reloadShaders()

    # Records the state of the arrow keys
    def setKey(self, key, value):
        self.keyMap[key] = value

    def prepareSRGB(self, np):
        """ Sets the correct texture format for all textures found in <np> """
        for tex in np.findAllTextures():

            baseFormat = tex.getFormat()

            if baseFormat == Texture.FRgb:
                tex.setFormat(Texture.FSrgb)
            elif baseFormat == Texture.FRgba:
                tex.setFormat(Texture.FSrgbAlpha)
            else:
                print "Unkown texture format:", baseFormat
                print "\tTexture:", tex

            # tex.setMinfilter(Texture.FTLinearMipmapLinear)
            # tex.setMagfilter(Texture.FTLinear)
            tex.setAnisotropicDegree(16)

    # Accepts arrow keys to move either the player or the menu cursor,
    # Also deals with grid checking and collision detection
    def move(self, task):

        # If the camera-left key is pressed, move camera left.
        # If the camera-right key is pressed, move camera right.

        base.camera.lookAt(self.ralph)
        if (self.keyMap["cam-left"] != 0):
            base.camera.setX(base.camera, -20 * globalClock.getDt())
        if (self.keyMap["cam-right"] != 0):
            base.camera.setX(base.camera, +20 * globalClock.getDt())

        # save ralph's initial position so that we can restore it,
        # in case he falls off the map or runs into something.

        startpos = self.ralph.getPos()

        # If a move-key is pressed, move ralph in the specified direction.

        if (self.keyMap["left"] != 0):
            self.ralph.setH(self.ralph.getH() + 300 * globalClock.getDt())
        if (self.keyMap["right"] != 0):
            self.ralph.setH(self.ralph.getH() - 300 * globalClock.getDt())
        if (self.keyMap["forward"] != 0):
            self.ralph.setY(self.ralph, -25 * globalClock.getDt())

        # If ralph is moving, loop the run animation.
        # If he is standing still, stop the animation.

        if (self.keyMap["forward"] != 0) or (self.keyMap["left"] != 0) or (self.keyMap["right"] != 0):
            if self.isMoving is False:
                self.ralph.loop("run")
                self.isMoving = True
        else:
            if self.isMoving:
                self.ralph.stop()
                self.ralph.pose("walk", 5)
                self.isMoving = False

        # If the camera is too far from ralph, move it closer.
        # If the camera is too close to ralph, move it farther.

        camvec = self.ralph.getPos() - base.camera.getPos()
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()
        if (camdist > 7.0):
            base.camera.setPos(base.camera.getPos() + camvec * (camdist - 7))
            camdist = 7.0
        if (camdist < 5.0):
            base.camera.setPos(base.camera.getPos() - camvec * (5 - camdist))
            camdist = 5.0

        # Now check for collisions.

        self.cTrav.traverse(render)

        # Adjust ralph's Z coordinate.  If ralph's ray hit terrain,
        # update his Z. If it hit anything else, or didn't hit anything, put
        # him back where he was last frame.

        entries = []
        for i in range(self.ralphGroundHandler.getNumEntries()):
            entry = self.ralphGroundHandler.getEntry(i)
            entries.append(entry)
        entries.sort(lambda x, y: cmp(y.getSurfacePoint(render).getZ(),
                                      x.getSurfacePoint(render).getZ()))
        if (len(entries) > 0) and (entries[0].getIntoNode().getName() == "terrain"):
            self.ralph.setZ(entries[0].getSurfacePoint(render).getZ())
        else:
            self.ralph.setPos(startpos)

        # Keep the camera at one foot above the terrain,
        # or two feet above ralph, whichever is greater.

        entries = []
        for i in range(self.camGroundHandler.getNumEntries()):
            entry = self.camGroundHandler.getEntry(i)
            entries.append(entry)
        entries.sort(lambda x, y: cmp(y.getSurfacePoint(render).getZ(),
                                      x.getSurfacePoint(render).getZ()))
        if (len(entries) > 0) and (entries[0].getIntoNode().getName() == "terrain"):
            base.camera.setZ(entries[0].getSurfacePoint(render).getZ() + 1.0)
        if (base.camera.getZ() < self.ralph.getZ() + 2.5):
            base.camera.setZ(self.ralph.getZ() + 2.5)

        # The camera should look in ralph's direction,
        # but it should also try to stay horizontal, so look at
        # a floater which hovers above ralph's head.

        self.floater.setPos(self.ralph.getPos())
        self.floater.setZ(self.ralph.getZ() + 2.0)
        base.camera.lookAt(self.floater)

        return task.cont


w = World()
w.run()
