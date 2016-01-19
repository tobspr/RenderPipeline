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

from panda3d.core import PTAInt, Texture, Shader

from .Util.DebugObject import DebugObject
from .Util.Image import Image
from .RenderTarget import RenderTarget

from .Native import GPUCommand, GPUCommandList

class GPUCommandQueue(DebugObject):

    """ This class offers an interface to the gpu, allowing commands to be
    pushed to a queue which then get executed on the gpu """

    def __init__(self, pipeline):
        DebugObject.__init__(self, "GPUCommandQueue")
        self._pipeline = pipeline
        self._commands_per_frame = 512
        self._command_list = GPUCommandList()
        self._pta_num_commands = PTAInt.empty_array(1)
        self._create_data_storage()
        self._create_command_target()
        self._commands = []
        self._register_defines()

    def clear_queue(self):
        """ Clears all commands currently being in the queue """
        raise NotImplementedError()

    def get_cmd_list(self):
        """ Returns a handle to the command list """
        return self._command_list

    def get_num_queued_commands(self):
        """ Returns the amount of queued commands, which are waiting to get
        executed on the gpu. This might be zero a lot of the time, because the
        GPUCommandList clears the queue after executing, so you have to call
        this after work was submitted. """
        return self._command_list.get_num_commands()

    def get_num_processed_commands(self):
        """ Returns the amount of commands processed the last time when the
        command queue was updated """
        return self._pta_num_commands[0]

    def process_queue(self):
        """ Processes the n first commands of the queue """
        pointer = self._data_texture.modify_ram_image()
        num_commands_exec = self._command_list.write_commands_to(
            pointer, self._commands_per_frame)
        self._pta_num_commands[0] = num_commands_exec

    def reload_shaders(self):
        """ Reloads the command shader """
        shader = Shader.load(Shader.SL_GLSL,
                             "Shader/DefaultPostProcess.vert.glsl",
                             "Shader/ProcessCommandQueue.fragment.glsl")
        self._command_target.set_shader(shader)

    def register_input(self, key, val):
        """ Registers an new shader input to the command target """
        self._command_target.set_shader_input(key, val)

    def _register_defines(self):
        """ Registers all the command types as defines so they can be used
        in a shader later on """
        for attr in dir(GPUCommand):
            if attr.startswith("CMD_"):
                attr_val = getattr(GPUCommand, attr)
                self._pipeline.stage_mgr.define(attr, attr_val)
        self._pipeline.stage_mgr.define("GPU_CMD_INT_AS_FLOAT",
            GPUCommand.get_uses_integer_packing())

    def _create_data_storage(self):
        """ Creates the buffer used to transfer commands """
        command_buffer_size = self._commands_per_frame * 32
        self.debug("Allocating command buffer of size", command_buffer_size)
        self._data_texture = Image.create_buffer(
            "CommandQueue", command_buffer_size, Texture.T_float, Texture.F_r32)
        self._data_texture.set_clear_color(0)

    def _create_command_target(self):
        """ Creates the target which processes the commands """
        self._command_target = RenderTarget("CommandTarget")
        self._command_target.set_size(1, 1)
        self._command_target.prepare_offscreen_buffer()
        self._command_target.set_shader_input("CommandQueue", self._data_texture)
        self._command_target.set_shader_input("commandCount", self._pta_num_commands)
