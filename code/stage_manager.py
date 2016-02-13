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
from six import iteritems

import time

from panda3d.core import Texture
from direct.stdpy.file import open

from .globals import Globals
from .gui.pipe_viewer import PipeViewer
from .rp_object import RPObject
from .util.image import Image
from .util.shader_ubo import BaseUBO
from .external.yaml import load_yaml_file

from .stages.update_previous_pipes_stage import UpdatePreviousPipesStage
from .base_manager import BaseManager

class StageManager(BaseManager):

    """ This manager takes a list of RenderStages and puts them into an order,
    while connecting the different pipes, inputs, ubos and defines. """

    def __init__(self, pipeline):
        """ Constructs the stage manager """
        BaseManager.__init__(self)
        self._stages = []
        self._inputs = {}
        self._pipes = {}
        self._ubos = {}
        self._previous_pipes = {}
        self._defines = {}
        self._pipeline = pipeline
        self._created = False

        self._load_stage_order()

        # Register the manager so the pipe viewer can read our data
        PipeViewer.register_stage_mgr(self)

    def _load_stage_order(self):
        """ Loads the order of all stages from the stages.yaml configuration
        file """
        orders = load_yaml_file("config/stages.yaml")
        if "global_stage_order" not in orders:
            self.error("Could not load stage order, root key does not exist!")
            return
        self._stage_order = orders["global_stage_order"]

    def add_stage(self, stage):
        """ Adds a new stage """
        if stage.stage_id not in self._stage_order:
            self.error("They stage type", stage.get_name(),
                       "is not registered yet! Please add it to the StageManager!")
            return

        if self._created:
            self.error("Cannot attach stage, stages are already created!")
            return

        if not stage.is_enabled():
            self.debug("Skipping disabled stage", stage)
            return

        self._stages.append(stage)

    def add_input(self, key, value):
        """ Registers a new shader input """
        self._inputs[key] = value

    def add_ubo(self, handle):
        """ Registers a new uniform buffer object """
        self._ubos[handle.get_name()] = handle

    def define(self, key, value):
        """ Registers a new define for the shader auto config """
        self._defines[key] = value

    def remove_define_if(self, condition):
        """ Removes all defines matching condition, condition should be a
        function or lambda taking 1 argument (the name of the define). """
        to_remove = []
        for define in self._defines:
            if condition(define):
                to_remove.append(define)

        for define in to_remove:
            del self._defines[define]

    def get_pipe(self, pipe_name):
        """ Returns a handle to an existing pipe """
        return self._pipes[pipe_name]

    def has_pipe(self, pipe_name):
        """ Returns whether a certain pipe exists """
        return pipe_name in self._pipes

    def _prepare_stages(self):
        """ Prepares all stages by removing disabled stages and sorting stages
        by order """

        # Remove all disabled stages
        to_remove = []
        for stage in self._stages:
            if not stage.is_enabled():
                to_remove.append(stage)

        for stage in to_remove:
            self._stages.remove(stage)

        self._stages.sort(key=lambda stage: self._stage_order.index(stage.stage_id))

    def _bind_pipes_to_stage(self, stage):
        """ Sets all required pipes on a stage """
        for pipe in stage.required_pipes:
            if pipe in self._ubos:
                self._ubos[pipe].bind_to(stage)
                continue

            if pipe.startswith("PreviousFrame::"):
                # Special case: Pipes from the previous frame. We assume those
                # pipes have the same size as the window and a format of
                # F_rgba16. Could be subject to change.
                pipe_name = pipe.split("::")[-1]
                if pipe_name not in self._previous_pipes:
                    self.debug("Storing previous frame pipe for " + pipe_name)
                    pipe_tex = Image.create_2d(
                        "Prev-" + pipe_name, Globals.base.win.get_x_size(),
                        Globals.base.win.get_y_size(), Texture.T_float,
                        Texture.F_rgba16)
                    pipe_tex.clear_image()
                    self._previous_pipes[pipe_name] = pipe_tex
                stage.set_shader_input("Previous_" + pipe_name, self._previous_pipes[pipe_name])
                continue

            if pipe not in self._pipes:
                self.error("Pipe '" + pipe + "' is missing for", stage)
                return False

            pipe_value = self._pipes[pipe]
            if isinstance(pipe_value, list) or isinstance(pipe_value, tuple):
                stage.set_shader_input(pipe, *pipe_value)
            else:
                stage.set_shader_input(pipe, pipe_value)
        return True

    def _bind_inputs_to_stage(self, stage):
        """ Binds all inputs including common inputs to the given stage """
        common_inputs = ["mainCam", "mainRender", "MainSceneData", "TimeOfDay"]

        # Check if all inputs are available, and set them
        for input_binding in stage.required_inputs + common_inputs:
            if input_binding not in self._inputs and \
               input_binding not in self._ubos:
                self.error("Input", input_binding, "is missing for", stage)
                continue

            if input_binding in self._inputs:
                stage.set_shader_input(input_binding,
                                       self._inputs[input_binding])
            elif input_binding in self._ubos:
                self._ubos[input_binding].bind_to(stage)
            else:
                assert False
        return True

    def _register_stage_outcome(self, stage):
        """ Registers all produced pipes, inputs and defines from the given
        stage, so they can be used by later stages. """

        # Register all the new pipes, inputs and defines
        for pipe_name, pipe_data in iteritems(stage.produced_pipes):
            if isinstance(pipe_data, BaseUBO):
                self._ubos[pipe_name] = pipe_data
                continue

            self._pipes[pipe_name] = pipe_data

        for define_name, data in iteritems(stage.produced_defines):
            if define_name in self._defines:
                self.warn("Stage", stage, "overrides define", define_name)
            self._defines[define_name] = data

        for input_name, data in iteritems(stage.produced_inputs):
            if input_name in self._inputs:
                self.warn("Stage", stage, "overrides input", input_name)

            # Check for UBO's
            if isinstance(data, BaseUBO):
                self._ubos[input_name] = data
                continue

            self._inputs[input_name] = data

    def _create_previous_pipes(self):
        """ Creates a target for each last-frame's pipe """
        # Finally create the stage which stores all the current pipes in the
        # previous pipes textures:
        if self._previous_pipes:
            self._prev_stage = UpdatePreviousPipesStage(self._pipeline)

            for prev_pipe, prev_tex in iteritems(self._previous_pipes):

                if prev_pipe not in self._pipes:
                    self.error("Attempted to use previous frame data from pipe",
                               prev_pipe, "- however, that pipe was never created!")
                    return False

                # Tell the stage to transfer the data from the current pipe to
                # the current texture
                self._prev_stage.add_transfer(self._pipes[prev_pipe], prev_tex)

            self._prev_stage.create()
            self._stages.append(self._prev_stage)

    def setup(self):
        """ Setups the stages """
        self.debug("Setup stages ...")

        self._created = True
        self._prepare_stages()

        # Process each stage
        for stage in self._stages:
            stage.create()

            # Rely on the methods to print an appropriate error message
            if not self._bind_pipes_to_stage(stage):
                continue
            if not self._bind_inputs_to_stage(stage):
                continue

            self._register_stage_outcome(stage)

        self._create_previous_pipes()

    def set_shaders(self):
        """ This pass sets the shaders to all passes and also generates the
        shader configuration """

        # First genereate the auto config
        self.write_autoconfig()

        # Then generate the shaders
        for stage in self._stages:
            stage.set_shaders()

    def do_update(self):
        """ Calls the update method for each registered stage """
        for stage in self._stages:
            stage.update()

    def _make_glsl_define(self, key, value):
        """ Given a define name and value, returns a glsl string which can be
        used to set that define in glsl """
        if isinstance(value, bool):
            # Cannot cast bools to string directly
            value = 1 if value else 0
        return "#define " + key + " " + str(value) + "\n"

    def write_autoconfig(self):
        """ Writes the shader auto config, based on the defines specified by the
        different stages """

        self.debug("Writing shader autoconfig")

        # Generate autoconfig as string
        output = "#pragma once\n\n"
        output += "// Autogenerated by RenderingPipeline\n"
        output += "// Do not edit! Your changes will be lost.\n\n"

        for key, value in sorted(iteritems(self._defines)):
            output += self._make_glsl_define(key, value)

        # Write a random timestamp, to make sure no caching occurs
        output += "#define RANDOM_TIMESTAMP " + str(time.time()) + "\n"

        # Try to write the file
        try:
            with open("$$pipeline_temp/$$pipeline_shader_config.inc.glsl", "w") as handle:
                handle.write(output)
        except IOError as msg:
            self.error("Error writing shader autoconfig:", msg)
