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

import copy

from six import iteritems, iterkeys

from panda3d.core import Shader, Filename

from .rp_object import RPObject
from .external.yaml import load_yaml_file
from .util.shader_template import ShaderTemplate

class Effect(RPObject):

    """ This class represents an instance of a compiled effect. It can be loaded
    from a File. """

    _DEFAULT_OPTIONS = {
        "render_gbuffer": True,
        "render_shadows": True,
        "render_voxel": True,
        "alpha_testing": True,
        "normal_mapping": True,
        "parallax_mapping": False,
    }

    _PASSES = ("gbuffer", "shadows", "voxelize")
    _GLOBAL_CACHE = {}
    _EFFECT_ID = 0

    @classmethod
    def load(cls, filename, options):
        """ Loads an effect from a given filename with the specified options.
        This lookups in the global effect cache, and checks if a similar effect
        (i.e. with the same hash) was already loaded, and in that case returns it.
        Otherwise a new effect with the given options is created. """
        effect_hash = cls._generate_hash(filename, options)
        if effect_hash in cls._GLOBAL_CACHE:
            return cls._GLOBAL_CACHE[effect_hash]
        effect = cls()
        effect.set_options(options)
        if not effect._load(filename):
            RPObject.global_error("Effect", "Could not load effect!")
            return None
        return effect

    @classmethod
    def _generate_hash(cls, filename, options):
        """ Generates an unique hash based on the effect path and options. The
        effect hash is based on the filename and the configured options, and
        is ensured to make the effect unique. This is important to make sure
        the caching works as intended. """
        constructed_dict = {}
        for key in sorted(iterkeys(cls._DEFAULT_OPTIONS)):
            if key in options:
                val = options[key]
            else:
                val = cls._DEFAULT_OPTIONS[key]
            constructed_dict[key] = val

        # Hash filename, make sure it has the right format before tho
        fname = Filename(filename)
        fname.make_absolute()
        fhash = str(hash(fname.to_os_generic()))

        # Hash the options
        to_str = lambda v: "1" if v else "0"
        opt_hash = ''.join([
            to_str(options[k]) if k in options else to_str(cls._DEFAULT_OPTIONS[k])
            for k in sorted(cls._DEFAULT_OPTIONS)])

        return fhash + "-" + opt_hash

    def __init__(self):
        """ Constructs a new empty effect """
        RPObject.__init__(self)
        self._effect_id = Effect._EFFECT_ID
        Effect._EFFECT_ID += 1
        self._options = copy.deepcopy(self._DEFAULT_OPTIONS)
        self._source = ""

    @property
    def effect_id(self):
        """ Returns a unique id for the effect """
        return self._effect_id

    def get_option(self, name):
        """ Returns a given option value by name """
        return self._options[name]

    def set_options(self, options):
        """ Sets the effect options, overriding the default options """
        for key, val in iteritems(options):
            if key not in self._options:
                self.error("Unkown option:", key)
                continue
            self._options[key] = val

    def _load(self, filename):
        """ Loads the effect from the given filename """
        self._source = filename
        self._effect_name = self._convert_filename_to_name(filename)
        self._shader_paths = {}
        self._effect_hash = self._generate_hash(filename, self._options)
        self._shader_objs = {}

        # Load the YAML file
        parsed_yaml = load_yaml_file(filename)
        self._parse_content(parsed_yaml)

        # Construct a shader for each pass
        for pass_id in self._PASSES:
            vertex_src = self._shader_paths["vertex"]
            fragment_src = self._shader_paths[pass_id]
            self._shader_objs[pass_id] = Shader.load(
                Shader.SL_GLSL, vertex_src, fragment_src)

        return True

    def get_shader_obj(self, pass_id):
        if pass_id not in self._shader_objs:
            self.warn("Pass '" + pass_id + "' not found!")
            return False
        return self._shader_objs[pass_id]

    def _convert_filename_to_name(self, filename):
        """ Constructs an effect name from a filename """
        return filename.replace(".yaml", "").replace("effects/", "")\
            .replace("/", "_").replace("\\", "_").replace(".", "-")

    def _parse_content(self, parsed_yaml):
        """ Internal method to construct the effect from a yaml object """
        for key, val in iteritems(parsed_yaml):
            self._parse_shader_template(key, val)

        # Create missing programs using the default options
        if "vertex" not in parsed_yaml:
            self._parse_shader_template("vertex", {})

        for key in self._PASSES:
            if key not in parsed_yaml:
                self._parse_shader_template(key, {})

    def _parse_shader_template(self, shader_id, data):
        """ Parses a fragment template """
        shader_ext = "vert" if shader_id == "vertex" else "frag"
        default_template = "$$shader/templates/{}.{}.glsl".format(shader_id, shader_ext)
        shader_path = self._construct_shader_from_data(shader_id, default_template, data)
        self._shader_paths[shader_id] = shader_path

    def _construct_shader_from_data(self, shader_id, default_template, data):
        """ Constructs a shader from a given dataset """
        injects = {}
        template_src = default_template

        # Check the template
        if "template" in data:
            data_template = data["template"]
            if data_template != "default":
                template_src = data_template

        # Add defines to the injects
        injects['defines'] = []
        for key, val in iteritems(self._options):
            val_str = str(val)
            if isinstance(val, bool):
                val_str = "1" if val else "0"
            injects['defines'].append("#define OPT_" + key.upper() + " " + val_str)

        # Parse dependencies
        if "dependencies" in data:
            injects["includes"] = []
            for dependency in data["dependencies"]:
                include_str = "#pragma include \"" + dependency + "\""
                injects["includes"].append(include_str)

        # Append inouts
        if "inout" in data:
            injects["inout"] = data["inout"]

        # Append aditional injects
        if "inject" in data:
            data_injects = data["inject"]
            for key, val in iteritems(data_injects):
                if val is None:
                    self.warn("Empty insertion: '" + key + "'")
                    continue

                if isinstance(val, (list, tuple)):
                    self.warn("Invalid syntax, you used a list but you should have used a string:")
                    self.warn(val)
                    continue
                val = [i for i in val.split("\n")]

                if key in injects:
                    injects[key] += val
                else:
                    injects[key] = val

        # Check for unrecognized keys
        for key in data:
            if key not in ["dependencies", "inout", "inject", "template"]:
                self.warn("Unrecognized key:", key)

        shader = ShaderTemplate(
            template_src,
            self._effect_name + "@" + shader_id + "@" + self._effect_hash)

        for key, val in iteritems(injects):
            shader.register_template_value(key, val)

        return shader.create()
