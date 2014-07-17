
from panda3d.core import ModifierButtons, Vec3, PStatClient


class MovementController:

    def __init__(self, showbase):
        self.showbase = showbase
        self.movement = [0, 0, 0]
        self.velocity = Vec3(0.0)
        self.hprMovement = [0,0]
        self.speed = 0.2
        self.initialPosition = Vec3(0)
        self.initialDestination = Vec3(0)
        self.mouseEnabled = False
        self.lastMousePos = [0,0]
        self.mouseSensivity = 0.7
        self.keyboardHprSpeed = 0.8


    def setInitialPosition(self, pos, target):
        self.initialPosition = pos
        self.initialDestination = target
        self._resetToInitial()

    def _resetToInitial(self):
        self.showbase.camera.setPos(self.initialPosition)
        self.showbase.camera.lookAt(
            self.initialDestination.x, self.initialDestination.y, self.initialDestination.z)



    # Key handler
    def _setMovement(self, direction, amount):
        self.movement[direction] = amount

    # Keyboard handler for camera rotation
    def _setHprMovement(self, direction, amount):
        self.hprMovement[direction] = amount


    # Mouse handler
    def _setMouseEnabled(self, enabled):
        self.mouseEnabled = enabled

    # Increases movement speed
    def _increaseSpeed(self):
        self.speed *= 1.4

    # Decreases movement speed
    def _decreaseSpeed(self):
        self.speed *= 0.6

    # Unbinds the movement controler and restores the previous state
    def unbind(self):
        raise NotImplementedError()

    # Attaches the movement controler
    def setup(self):

        # Setup keybindings

        # x
        self.showbase.accept("w",       self._setMovement, [0, 1])
        self.showbase.accept("w-up",    self._setMovement, [0, 0])
        self.showbase.accept("s",       self._setMovement, [0, -1])
        self.showbase.accept("s-up",    self._setMovement, [0, 0])

        # y
        self.showbase.accept("a",       self._setMovement, [1, -1])
        self.showbase.accept("a-up",    self._setMovement, [1, 0])
        self.showbase.accept("d",       self._setMovement, [1, 1])
        self.showbase.accept("d-up",    self._setMovement, [1, 0])

        # z
        self.showbase.accept("space",   self._setMovement, [2, 1])
        self.showbase.accept("space-up", self._setMovement, [2, 0])
        self.showbase.accept("shift",   self._setMovement, [2, -1])
        self.showbase.accept("shift-up", self._setMovement, [2, 0])

        # wireframe + debug + buffer viewer
        self.showbase.accept("f3", self.showbase.toggleWireframe)
        self.showbase.accept("p",  self._showDebugOutput)
        self.showbase.accept("v",  self._toggleBufferViewer)

        # mouse
        self.showbase.accept("mouse1",    self._setMouseEnabled, [True])
        self.showbase.accept("mouse1-up", self._setMouseEnabled, [False])

        # arrow mouse navigation
        self.showbase.accept("arrow_up",        self._setHprMovement, [1, 1])
        self.showbase.accept("arrow_up-up",     self._setHprMovement, [1, 0])
        self.showbase.accept("arrow_down",      self._setHprMovement, [1, -1])
        self.showbase.accept("arrow_down-up",   self._setHprMovement, [1, 0])
        self.showbase.accept("arrow_left",      self._setHprMovement, [0, 1])
        self.showbase.accept("arrow_left-up",   self._setHprMovement, [0, 0])
        self.showbase.accept("arrow_right",     self._setHprMovement, [0, -1])
        self.showbase.accept("arrow_right-up",  self._setHprMovement, [0, 0])


        # increase / decrease speed
        self.showbase.accept("+", self._increaseSpeed)
        self.showbase.accept("-", self._decreaseSpeed)

        # disable modifier buttons to be able to move while pressing shift for
        # example
        self.showbase.mouseWatcherNode.setModifierButtons(ModifierButtons())
        self.showbase.buttonThrowers[
            0].node().setModifierButtons(ModifierButtons())

        # disable pandas builtin mouse control
        self.showbase.disableMouse()

        # add ourself as an update task
        self.showbase.addTask(
            self._update, "updateMovementController", priority=90)


        self.showbase.accept("1", PStatClient.connect)
        self.showbase.accept("3", self._resetToInitial)

    # Internal method to trigger buffer viewer
    def _toggleBufferViewer(self):
        print "Toggling buffer viewer"
        self.showbase.bufferViewer.toggleEnable()

    # Invernal update method
    def _update(self, task):

        # Update mouse first
        if self.showbase.mouseWatcherNode.hasMouse():
            x = self.showbase.mouseWatcherNode.getMouseX()
            y = self.showbase.mouseWatcherNode.getMouseY()
            self.currentMousePos = [x * 90 * self.mouseSensivity, y * 70 * self.mouseSensivity]

            if self.mouseEnabled:
                diffx = self.lastMousePos[0] - self.currentMousePos[0]
                diffy = self.lastMousePos[1] - self.currentMousePos[1]

                # no move on the beginning
                if self.lastMousePos[0] == 0 and self.lastMousePos[1] == 0:
                    diffx = 0
                    diffy = 0

                self.showbase.camera.setH(self.showbase.camera.getH() + diffx)
                self.showbase.camera.setP(self.showbase.camera.getP() - diffy)

            self.lastMousePos = self.currentMousePos[:]

        # Compute movement in render space
        movementDirection = (Vec3(self.movement[1], self.movement[0], 0)
                             * self.speed
                             * self.showbase.taskMgr.globalClock.getDt() * 100.0)

        # Transform by camera direction
        cameraQuaternion = self.showbase.camera.getQuat(self.showbase.render)
        translatedDirection = cameraQuaternion.xform(movementDirection)
      

        # zforce is independent of camera direction
        translatedDirection.addZ(
            self.movement[2] * self.showbase.taskMgr.globalClock.getDt() * 40.0 * self.speed)



        self.velocity += translatedDirection*0.15
        self.velocity *= 0.9
  

        # apply new position
        self.showbase.camera.setPos(
            self.showbase.camera.getPos() + self.velocity)

        # transform rotation (keyboard keys)
        rotationSpeed = self.keyboardHprSpeed * 100.0 * self.showbase.taskMgr.globalClock.getDt()
        self.showbase.camera.setHpr(self.showbase.camera.getHpr() + Vec3(self.hprMovement[0],self.hprMovement[1],0) * rotationSpeed )

        return task.cont


    # Shows debug options
    def _showDebugOutput(self):
        print "\n" * 5
        print "DEBUG MENU"
        print "-" * 50
        print "Select an option:"
        print "\t(1) Connect to pstats"
        print "\t(2) Toggle frame rate meter"
        print "\t(3) Reset to initial position"
        print "\t(4) Display camera position"
        print "\t(5) Show scene graph"
        print "\t(6) Open placement window"
        print

        selectedOption = raw_input("Which do you want to choose?: ")

        try:
            selectedOption = int(selectedOption.strip())
        except:
            print "Option has to be a valid number!"
            return False

        if selectedOption < 1 or selectedOption > 6:
            print "Invalid option!"
            return False

        # pstats
        if selectedOption == 1:
            print "Connecting to pstats .."
            print "If you have no pstats running, this will take 5 seconds to timeout .."
            PStatClient.connect()

        # frame rate meter
        elif selectedOption == 2:
            print "Toggling frame rate meter .."
            self.showbase.setFrameRateMeter(not self.showbase.frameRateMeter)

        # initial position
        elif selectedOption == 3:
            print "Reseting camera position / hpr .."
            self._resetToInitial()

        # display camera pos
        elif selectedOption == 4:
            print "Debug information:"
            print "\tCamera is at", self.showbase.camera.getPos(self.showbase.render)
            print "\tCamera hpr is", self.showbase.camera.getHpr(self.showbase.render)

        # show scene graph
        elif selectedOption == 5:
            print "SCENE GRAPH:"
            print "-" * 50
            self.showbase.render.ls()
            print "-" * 50
            print
            print "ANALYZED:"
            print "-" * 50
            self.showbase.render.analyze()
            print "-" * 50

        # placement window
        elif selectedOption == 6:
            print "Opening placement window. You need tkinter installed to be able to use it"
            self.showbase.render.place()
            # print "It seems .place() is currently not working. Sorry!!"
