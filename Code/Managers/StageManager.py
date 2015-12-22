
import time

from panda3d.core import Texture
from direct.stdpy.file import open

from ..Globals import Globals
from ..GUI.PipeViewer import PipeViewer
from ..Util.DebugObject import DebugObject
from ..Util.Image import Image
from ..Util.ShaderUBO import BaseUBO

from ..Stages.UpdatePreviousPipesStage import UpdatePreviousPipesStage
from ..BaseManager import BaseManager

class StageManager(BaseManager):
    """ This manager takes a list of RenderStages and puts them into an order,
    and also connects the different pipes """

    # This defines the order of all stages, in case they are attached
    _STAGE_ORDER = [
        "GBufferStage",
        "PSSMShadowStage",
        "DownscaleZStage",
        "ReprojectStage",
        "FlagUsedCellsStage",
        "CollectUsedCellsStage",
        "CullLightsStage",
        "AOStage",
        "ApplyLightsStage",
        "PSSMStage",
        "ScatteringStage",
        "AmbientStage",
        "SSLRStage",
        "SMAAStage",
        "BloomStage",
        "FinalStage",
        "ColorCorrectionStage",
        "UpdatePreviousPipesStage"
    ]

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

        # Register the manager so the pipe viewer can read our data
        PipeViewer.register_stage_mgr(self)

    def add_stage(self, stage):
        """ Adds a new stage """
        if stage.get_stage_id() not in self._STAGE_ORDER:
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

    def setup(self):
        """ Setups the stages """
        self.debug("Setup stages ...")

        self._created = True

        # Remove all disabled stages
        to_remove = []
        for stage in self._stages:
            if not stage.is_enabled():
                to_remove.append(stage)

        for stage in to_remove:
            self._stages.remove(stage)

        # Sort stages
        self._stages.sort(key=lambda stage: self._STAGE_ORDER.index(
            stage.get_stage_id()))

        # Process each stage
        for stage in self._stages:
            stage.create()

            # Check if all pipes are available, and set them
            for pipe in stage.get_input_pipes():


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
                        pipe_tex.get_texture().clear_image()
                        self._previous_pipes[pipe_name] = pipe_tex.get_texture()
                    stage.set_shader_input("Previous_" + pipe_name, self._previous_pipes[pipe_name])
                    continue

                if pipe not in self._pipes:
                    self.error("Pipe '" + pipe + "' is missing for", stage)
                    continue

                pipe_value = self._pipes[pipe]
                if isinstance(pipe_value, list) or isinstance(pipe_value, tuple):
                    stage.set_shader_input(pipe, *pipe_value)
                else:
                    stage.set_shader_input(pipe, pipe_value)

            # Check if all inputs are available, and set them
            for input_binding in stage.get_required_inputs():
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

            # Register all the new pipes, inputs and defines
            for pipe_name, pipe_data in list(stage.get_produced_pipes().items()):
                # Check for UBO's
                if isinstance(pipe_data, BaseUBO):
                    self._ubos[pipe_name] = pipe_data
                    continue

                self._pipes[pipe_name] = pipe_data

            for define_name, data in list(stage.get_produced_defines().items()):
                if define_name in self._defines:
                    self.warn("Stage", stage, "overrides define", define_name)
                self._defines[define_name] = data

            for input_name, data in list(stage.get_produced_inputs().items()):
                if input_name in self._inputs:
                    self.warn("Stage", stage, "overrides input", input_name)

                # Check for UBO's
                if isinstance(data, BaseUBO):
                    self._ubos[input_name] = data
                    continue

                self._inputs[input_name] = data

        # Finally create the stage which stores all the current pipes in the
        # previous pipes textures:
        if self._previous_pipes:
            self._prev_stage = UpdatePreviousPipesStage(self._pipeline)

            for prev_pipe, prev_tex in self._previous_pipes.items():

                if prev_pipe not in self._pipes:
                    self.error("Attempted to use previous frame data from pipe",
                               prev_pipe, "- however, that pipe was never created!")
                    continue

                # Tell the stage to transfer the data from the current pipe to
                # the current texture
                self._prev_stage.add_transfer(self._pipes[prev_pipe], prev_tex)

            self._prev_stage.create()
            self._stages.append(self._prev_stage)

    def set_shaders(self):
        """ This pass sets the shaders to all passes and also generates the
        shader auto config"""

        # First genereate the auto config
        self.write_autoconfig()

        # Then generate the shaders
        for stage in self._stages:
            stage.set_shaders()

    def do_update(self):
        """ Calls the update method for each stage """
        for stage in self._stages:
            stage.update()

    def write_autoconfig(self):
        """ Writes the shader auto config, based on the defines specified by the
        different stages """

        self.debug("Writing shader autoconfig")

        # Generate autoconfig as string
        output = "#pragma once\n\n"
        output += "// Autogenerated by RenderingPipeline\n"
        output += "// Do not edit! Your changes will be lost.\n\n"

        for key, value in sorted(self._defines.items()):
            # Cannot cast bools to string directly
            if isinstance(value, bool):
                value = 1 if value else 0
            output += "#define " + key + " " + str(value) + "\n"

        output += "#define RANDOM_TIMESTAMP " + str(time.time()) + "\n"

        # Try to write the file
        try:
            with open("$$PipelineTemp/$$ShaderAutoConfig.inc.glsl", "w") as handle:
                handle.write(output)
        except IOError as msg:
            self.error("Error writing shader autoconfig:", msg)
