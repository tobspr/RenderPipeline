"""

RenderPipeline

Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>

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

# Disable warning from pylint about the global attributes of the render stages,
# which may or may not be specified by subclasses.
# pylint: disable=E1101

import os

from panda3d.core import Shader

from .Util.DebugObject import DebugObject
from .RenderTarget import RenderTarget


class RenderStage(DebugObject):

    """ This class is the abstract class for all stages used in the pipeline.
    It represents a part of the pipeline render process. Each stage specifies
    which pipes it uses and which pipes it produces. A pipe can be seen as a
    texture, which gets modified. E.g. the gbuffer pass produces the gbuffer
    pipe, the ambient occlusion pass produces the occlusion pipe and so on. The
    lighting pass can then specify which pipes it needs and compute the image.
    Using a pipe system ensures that new techniques can be inserted easily,
    without the other techniques even being aware of them """

    @classmethod
    def add_input_requirement(cls, input_name):
        """ Adds a new input to the list of required inputs for this stage """
        if not hasattr(cls, "required_inputs"):
            DebugObject.global_warn("RenderStage", "The stage " + str(cls) +\
                " has no static input list! Can not call add_input_requirement.")
            return
        if input_name not in cls.required_inputs:
            cls.required_inputs.append(input_name)

    @classmethod
    def add_pipe_requirement(cls, pipe_name):
        """ Adds a new pipe to the list of required pipes for this stage """
        if not hasattr(cls, "required_pipes"):
            DebugObject.global_warn("RenderStage", "The stage " + str(cls) +\
                " has no static input pipe list! Can not call add_pipe_requirement.")
            return
        if pipe_name not in cls.required_pipes:
            cls.required_pipes.append(pipe_name)

    @classmethod
    def disable_stage(cls):
        """ Disables the stage, this will prevent the stage manager from creating
        this stage. This is mostly useful to replace the stage by another stage """
        cls.disabled = True

    @classmethod
    def is_enabled(cls):
        """ Returns whether the class is enabled or disabled """
        if hasattr(cls, "disabled") and cls.disabled:
            return False
        return True

    def __init__(self, stage_id, pipeline):
        """ Creates a new render stage """
        DebugObject.__init__(self, stage_id)
        self._stage_id = stage_id
        self._pipeline = pipeline
        self._targets = {}

    def get_stage_id(self):
        """ Returns the id of the stage """
        return self._stage_id

    def get_required_inputs(self):
        """ This method should return a list of shader inputs which are required
        for this stage """
        if hasattr(self, "required_inputs"):
            return self.required_inputs
        return []

    def get_input_pipes(self):
        """ This method should return which pipes are required for this stage.
        The key specifies the name under they will be available in the shader,
        while the value specifies the name of the pipe """
        if hasattr(self, "required_pipes"):
            return self.required_pipes
        return []

    def get_produced_pipes(self):
        """ This method should return which pipes this pass produces, the key
        specifies the name of the pipe, the value should be a handle to a
        Texture() """
        return {}

    def get_produced_inputs(self):
        """ This method should return all shader inputs which the pass returns
        as a dictionary, while the key specifies the name of the shader input
        and the value contains the input """
        return {}

    def get_produced_defines(self):
        """ This method should return a dictionary of all the defines which the
        pass produces """
        return {}

    def create(self):
        """ This method should setup the stage and create the pipes """
        raise NotImplementedError()

    def resize(self):
        """ This method gets called when the window resizes and should upate the
        pipes """
        raise NotImplementedError()

    def cleanup(self):
        """ This method should completely cleanup the stage and delete all used
        textures and render passes """
        raise NotImplementedError()

    def set_shaders(self):
        """ This method should set all required shaders, there should be no
        shaders set in the create method, because the shader auto config is not
        generated there """
        pass

    def set_shader_input(self, *args):
        """ This method sets a shader input on all stages, which is mainly used
        by the stage manager """
        for target in self._targets.values():
            target.set_shader_input(*args)

    def update(self):
        """ This method gets called every frame """
        pass

    def _create_target(self, name):
        """ Creates a new render target with the given name and attachs it to the
        list of targets """
        if name in self._targets:
            self.warn("Overriding existing target: " + name)
        self._targets[name] = RenderTarget(name)
        return self._targets[name]

    def _load_shader(self, *args):
        """ Loads a shader from the given args. If only one argument is passed,
        the default template for the stage is loaded. If two arguments are
        passed, the first argument should be the vertex shader and the second
        argument should be the fragment shader. If three arguments are passed,
        the order should be vertex, fragment, geometry """
        assert len(args) > 0 and len(args) <= 3
        args = ["Shader/" + i + ".glsl" if "$$PipelineTemp" not in i else i for i in args]

        # If only one shader is specified, assume its a postprocess fragment shader,
        # and use the default vertex shader
        if len(args) == 1:
            args = ["Shader/DefaultPostProcess.vert.glsl"] + args

        return Shader.load(Shader.SLGLSL, *args)

    def load_plugin_shader(self, *args):
        """ Loads a shader from the plugin directory. This method is useful
        for RenderStages created by plugins. For a description of the arguments,
        see the _load_shader function. """

        # The __module__ contains something like Plugins.XXX.YYY
        # We want XXX so we take the second parameter
        plugin_name = str(self.__class__.__module__).split(".")[1]

        plugin_loc = "Plugins/" + plugin_name + "/Shader/Stages/"
        path_args = [os.path.join(plugin_loc, i) if "$$PipelineTemp" not in i else i for i in args]
        path_args = [os.path.join(plugin_loc, i) if "$$PipelineTemp" not in i else i for i in args]

        # If only one shader is specified, assume its a postprocess fragment shader,
        # and use the default vertex shader
        if len(args) == 1:
            path_args = ["Shader/DefaultPostProcess.vert.glsl"] + path_args

        return Shader.load(Shader.SLGLSL, *path_args)
