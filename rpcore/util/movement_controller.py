"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""


# Disable the "exactly one space required after comma" message, for the input
# bindings it looks nicer to insert some spaces (see the setup method)
# pylint: disable=C0326

from __future__ import print_function

from panda3d.core import ModifierButtons, Vec3, PStatClient

class MovementController(object):

    """ This is a helper class, used to controll the camera and enable various
    debugging features. It is not really part of the pipeline, but included to
    view the demo scenes. """

    def __init__(self, showbase):
        self._showbase = showbase
        self._movement = [0, 0, 0]
        self._velocity = Vec3(0.0)
        self._hpr_movement = [0, 0]
        self._speed = 0.7
        self._initial_position = Vec3(0)
        self._initial_destination = Vec3(0)
        self._initial_hpr = Vec3(0)
        self._mouse_enabled = False
        self._last_mouse_pos = [0, 0]
        self._mouse_sensivity = 0.7
        self._keyboard_hpr_speed = 0.8
        self._use_hpr = False
        self._smoothness = 6.0
        self._bobbing_amount = 2.5
        self._bobbing_speed = 0.5

    def set_initial_position(self, pos, target):
        """ Sets the initial camera position """
        self._initial_position = pos
        self._initial_destination = target
        self._use_hpr = False
        self._reset_to_initial()

    def set_initial_position_hpr(self, pos, hpr):
        """ Sets the initial camera position """
        self._initial_position = pos
        self._initial_hpr = hpr
        self._use_hpr = True
        self._reset_to_initial()

    def _reset_to_initial(self):
        """ Resets the camera to the initial position """
        self._showbase.camera.set_pos(self._initial_position)

        if self._use_hpr:
            self._showbase.camera.set_hpr(self._initial_hpr)
        else:
            self._showbase.camera.look_at(
                self._initial_destination.x, self._initial_destination.y,
                self._initial_destination.z)

    def _set_movement(self, direction, amount):
        self._movement[direction] = amount

    def _set_hpr_movement(self, direction, amount):
        self._hpr_movement[direction] = amount

    def _set_mouse_enabled(self, enabled):
        self._mouse_enabled = enabled

    def _increase_speed(self):
        self._speed *= 1.4

    def _decrease_speed(self):
        self._speed *= 0.6

    def unbind(self):
        """ Unbinds the movement controler and restores the previous state """
        raise NotImplementedError()

    def setup(self):
        """ Attaches the movement controller and inits the keybindings """
        # x
        self._showbase.accept("raw-w",       self._set_movement, [0, 1])
        self._showbase.accept("raw-w-up",    self._set_movement, [0, 0])
        self._showbase.accept("raw-s",       self._set_movement, [0, -1])
        self._showbase.accept("raw-s-up",    self._set_movement, [0, 0])

        # y
        self._showbase.accept("raw-a",       self._set_movement, [1, -1])
        self._showbase.accept("raw-a-up",    self._set_movement, [1, 0])
        self._showbase.accept("raw-d",       self._set_movement, [1, 1])
        self._showbase.accept("raw-d-up",    self._set_movement, [1, 0])

        # z
        self._showbase.accept("space",   self._set_movement, [2, 1])
        self._showbase.accept("space-up", self._set_movement, [2, 0])
        self._showbase.accept("shift",   self._set_movement, [2, -1])
        self._showbase.accept("shift-up", self._set_movement, [2, 0])

        # wireframe + debug + buffer viewer
        self._showbase.accept("f3", self._showbase.toggleWireframe)
        self._showbase.accept("f11", self._showbase.win.saveScreenshot)

        # mouse
        self._showbase.accept("mouse1",    self._set_mouse_enabled, [True])
        self._showbase.accept("mouse1-up", self._set_mouse_enabled, [False])

        # arrow mouse navigation
        self._showbase.accept("arrow_up",        self._set_hpr_movement, [1, 1])
        self._showbase.accept("arrow_up-up",     self._set_hpr_movement, [1, 0])
        self._showbase.accept("arrow_down",      self._set_hpr_movement, [1, -1])
        self._showbase.accept("arrow_down-up",   self._set_hpr_movement, [1, 0])
        self._showbase.accept("arrow_left",      self._set_hpr_movement, [0, 1])
        self._showbase.accept("arrow_left-up",   self._set_hpr_movement, [0, 0])
        self._showbase.accept("arrow_right",     self._set_hpr_movement, [0, -1])
        self._showbase.accept("arrow_right-up",  self._set_hpr_movement, [0, 0])

        # increase / decrease speed
        self._showbase.accept("+", self._increase_speed)
        self._showbase.accept("-", self._decrease_speed)

        # disable modifier buttons to be able to move while pressing shift for
        # example
        self._showbase.mouseWatcherNode.set_modifier_buttons(ModifierButtons())
        self._showbase.buttonThrowers[0].node().set_modifier_buttons(ModifierButtons())

        # disable pandas builtin mouse control
        self._showbase.disableMouse()

        # add ourself as an update task which gets executed very early before
        # the rendering
        self._showbase.addTask(self._update, "RP_UpdateMovementController", priority=-1000)

        # Hotkeys to connect to pstats and reset the initial position
        self._showbase.accept("1", PStatClient.connect)
        self._showbase.accept("3", self._reset_to_initial)

    def _update(self, task):
        """ Internal update method """

        # Update mouse first
        if self._showbase.mouseWatcherNode.has_mouse():
            x = self._showbase.mouseWatcherNode.get_mouse_x()
            y = self._showbase.mouseWatcherNode.get_mouse_y()
            self._current_mouse_pos = [x * 90 * self._mouse_sensivity,
                                       y * 70 * self._mouse_sensivity]

            if self._mouse_enabled:
                diffx = self._last_mouse_pos[0] - self._current_mouse_pos[0]
                diffy = self._last_mouse_pos[1] - self._current_mouse_pos[1]

                # Don't move in the very beginning
                if self._last_mouse_pos[0] == 0 and self._last_mouse_pos[1] == 0:
                    diffx = 0
                    diffy = 0

                self._showbase.camera.set_h(self._showbase.camera.get_h() + diffx)
                self._showbase.camera.set_p(self._showbase.camera.get_p() - diffy)

            self._last_mouse_pos = self._current_mouse_pos[:]

        # Compute movement in render space
        movement_direction = (Vec3(self._movement[1], self._movement[0], 0)
                              * self._speed
                              * self._showbase.taskMgr.globalClock.get_dt() * 100.0)

        # transform by the camera direction
        camera_quaternion = self._showbase.camera.get_quat(self._showbase.render)
        translated_direction = camera_quaternion.xform(movement_direction)

        # z-force is independent of camera direction
        translated_direction.add_z(
            self._movement[2] * self._showbase.taskMgr.globalClock.get_dt() * 40.0 * self._speed)

        self._velocity += translated_direction*0.15

        # apply the new position
        self._showbase.camera.set_pos(self._showbase.camera.get_pos() + self._velocity)

        # transform rotation (keyboard keys)
        rotation_speed = self._keyboard_hpr_speed * 100.0
        rotation_speed *= self._showbase.taskMgr.globalClock.get_dt()
        self._showbase.camera.set_hpr(
            self._showbase.camera.get_hpr() + Vec3(
                self._hpr_movement[0], self._hpr_movement[1], 0) * rotation_speed)


        # bobbing
        rotation = (self._showbase.taskMgr.globalClock.get_frame_time() % self._bobbing_speed) / self._bobbing_speed
        rotation = (min(rotation, 1.0 - rotation) * 2.0 - 0.5) * 2.0
        rotation *= self._bobbing_amount
        rotation *= self._velocity.length() / self._speed * 0.5
        self._showbase.camera.set_r(rotation)

        # fade out velocity
        self._velocity = self._velocity * max(0.0,
            1.0 - self._showbase.taskMgr.globalClock.get_dt() * 60.0 / max(0.01, self._smoothness))
        return task.cont
