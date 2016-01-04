
import copy

from panda3d.core import Shader, Filename

from ..External.PyYAML import YAMLEasyLoad
from ..Util.DebugObject import DebugObject
from ..Util.ShaderTemplate import ShaderTemplate

class Effect(DebugObject):

    """ This class represents an instance of a compiled effect. It can be loaded
    from a File. """

    _DEFAULT_OPTIONS = {
        "render_gbuffer": True,
        "render_shadows": True,
        "alpha_testing": True,
        "normal_mapping": True,
        "parallax_mapping": True,
    }

    _PASSES = ["GBuffer", "Shadows", "Voxelize"]
    _EFFECT_ID = 0

    @classmethod
    def generate_hash(cls, filename, options):
        """ Generates an unique hash based on the effect path and options """
        constructed_dict = {}
        for key in sorted(Effect._DEFAULT_OPTIONS.keys()):
            if key in options:
                val = options[key]
            else:
                val = Effect._DEFAULT_OPTIONS[key]
            constructed_dict[key] = val

        # Hash filename, make sure it has the right format before tho
        fname = Filename(filename)
        fname.make_absolute()
        fhash = str(hash(fname.to_os_generic()))

        # Hash the options
        to_str = lambda v: "1" if v else "0"
        opt_hash = ''.join([to_str(options[k]) if k in options else to_str(cls._DEFAULT_OPTIONS[k]) for k in sorted(cls._DEFAULT_OPTIONS)])

        return fhash + "-" + opt_hash

    def __init__(self):
        """ Constructs a new empty effect """
        DebugObject.__init__(self)
        self._effect_id = Effect._EFFECT_ID
        Effect._EFFECT_ID += 1
        self._options = copy.deepcopy(self._DEFAULT_OPTIONS)
        self._source = ""

    def get_effect_id(self):
        """ Returns a unique id for the effect """
        return self._effect_id

    def get_option(self, name):
        """ Returns a given option value by name """
        return self._options[name]

    def set_options(self, options):
        """ Sets the effect options, overriding the default options """
        for key, val in list(options.items()):
            if key not in self._options:
                self.error("Unkown option:", key)
                continue
            self._options[key] = val

    def load(self, filename):
        """ Loads the effect from the given filename """
        self._source = filename
        self._effect_name = self._convert_filename_to_name(filename)
        self._shader_paths = {}
        self._effect_hash = self.generate_hash(filename, self._options)
        self._shader_objs = {}

        # Load the YAML file
        parsed_yaml = YAMLEasyLoad(filename)
        self._parse_content(parsed_yaml)

        # Construct a shader for each pass
        for pass_id in self._PASSES:
            vertex_src = self._shader_paths["Vertex"]
            fragment_src = self._shader_paths["Fragment." + pass_id]
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
        return filename.replace(".yaml", "").replace("Effects/", "")\
            .replace("/", "_").replace("\\", "_").replace(".", "-")

    def _parse_content(self, parsed_yaml):
        """ Internal method to construct the effect from a yaml object """
        for key, val in list(parsed_yaml.items()):
            self._parse_shader_template(key, val)

        # Create missing programs using the default options
        if "Vertex" not in parsed_yaml:
            self._parse_shader_template("Vertex", {})

        for key in self._PASSES:
            if "Fragment." + key not in parsed_yaml:
                self._parse_shader_template("Fragment." + key, {})


    def _parse_shader_template(self, shader_id, data):
        """ Parses a fragment template """
        default_template = "Shader/Templates/" + shader_id + ".templ.glsl"
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
        for key, val in list(self._options.items()):
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
            for key, val in list(data_injects.items()):
                if val is None:
                    self.warn("Empty insertion: '" + key + "'")
                    continue

                if isinstance(val, list) or isinstance(val, tuple):
                    self.warn("Invalid syntax, you used a list but you should have used a string:")
                    self.warn(val)
                    continue

                val = [i.strip() + ";" for i in val.strip(";").split(";")]
                if key in injects:
                    injects[key] += val
                else:
                    injects[key] = val

        # Check for unrecognized keys
        for key in data:
            if key not in ["dependencies", "inout", "inject", "template"]:
                self.warn("Unrecognized key:", key)

        shader = ShaderTemplate(template_src, self._effect_name + "@" + shader_id + "@" + self._effect_hash)

        for key, val in list(injects.items()):
            shader.register_template_value(key, val)

        return shader.create()
