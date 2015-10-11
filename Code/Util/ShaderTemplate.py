

from panda3d.core import Shader
from direct.stdpy.file import open

from DebugObject import DebugObject


class ShaderTemplate(DebugObject):

    """ This class manages the loading of shader templates, including the
    replacement of template parameters. """

    _CONSTRUCTED_SHADERS = 0

    def __init__(self, template_file, template_name = "template"):
        DebugObject.__init__(self)
        self.debug("Constructing from '" + template_file + "'")
        self._file_source = template_file
        self._template_values = {}
        self._template_name = template_name

    def register_template_value(self, key, val):
        """ Registers a new template value. The value may either be a list of
        strings or just a single string """
        if type(val) != list:
            val = [val]
        key = key.lower()

        if key in self._template_values:
            self._template_values[key] += val
        else:
            self._template_values[key] = val

    def create(self):
        """ Constructs a shader object from the template and returns the path
        to the compiled shader """

        with open(self._file_source, "r") as handle:
            shader_lines = handle.readlines()

        # Parse all shader lines
        parsed_lines = []
        for line in shader_lines:
            stripped_line = line.strip().lower()

            # Check if the current line is a hook
            if stripped_line.startswith("%") and stripped_line.endswith("%"):

                # If the line is a hook, get the hook name and save the
                # indentation so we can indent all injected lines properly.
                hook_name = stripped_line[1:-1]
                indentation = " " * (len(line) - len(line.lstrip()))
                parsed_lines.append(indentation + "// Hook '" + hook_name + "'")

                # Inject all registered template values into the hook
                if hook_name in self._template_values:
                    insertions = self._template_values[hook_name]
                    for line_i in insertions:
                        parsed_lines.append(indentation + line_i)
                    # Remove the value from the list so we can check which
                    # hooks were not found in the template
                    del self._template_values[hook_name]

                parsed_lines.append(indentation + "// End of hook '" + hook_name + "'");
            else:
                parsed_lines.append(line.rstrip())

        # Warn the user about all unused hooks
        for key in self._template_values:
            self.warn("Hook '" + key + "' not found in template '" + self._file_source + "'!")

        # Write the constructed shader and load it back
        shader_content = '\n'.join(parsed_lines)
        ShaderTemplate._CONSTRUCTED_SHADERS += 1
        temp_path = "$$PipelineTemp/Shader-" + str(self._CONSTRUCTED_SHADERS) +\
            "@@" + self._template_name + ".glsl"

        with open(temp_path, "w") as handle:
            handle.write(shader_content)

        return temp_path
