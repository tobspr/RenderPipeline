
import copy

from External.PyYAML import yaml


class Effect:

    _DEFAULT_OPTIONS = {

    }

    _PASSES = ["GBuffer", "Shadows", "Voxelize"]

    @classmethod
    def _generate_hash(cls, filename, options):
        """ Generates an unique hash based on the effect path and options """
        # TODO: Implement me
        return 1

    def __init__(self):
        """ Constructs a new empty effect """
        self._options = copy.deepcopy(self._DEFAULT_OPTIONS)
        self._source = ""

    def set_options(self, options):
        """ Sets the effect options, overriding the default options """
        for key, val in options.iteritems():
            if key not in self._options:
                print "ERROR: Unkown option:", key
                continue
            self._options[key] = val

    def load(self, filename):
        """ Loads the effect from the given filename """
        self._source = filename
        parsed_yaml = None

        # Get file content and parse it
        try:
            with open(filename, "r") as handle:
                parsed_yaml = yaml.load(handle)
        except IOError, msg:
            print "Could not find file:", filename, "!"
            print msg
            return False
        except yaml.YAMLError, msg:
            print "Could not parse file:", filename, "!"
            print msg
            return False

        self._parse_content(parsed_yaml)

    def _parse_content(self, parsed_yaml):
        """ Internal method to construct the effect from a yaml object """
        for key, val in parsed_yaml.iteritems():
            if key == "Vertex":
                self._parse_vertex_template(val)
            elif key.startswith("Fragment."):
                key_pass = key.replace("Fragment.", "")
                if key_pass in self._Passes:
                    self._parse_fragment_template(key_pass, val)
                else:
                    print "Error: Unrecognized pass:", key_pass
            else:
                print "Error: Unrecognized section:", key

    def _parse_vertex_template(self, vertex_data):
        """ Parses a vertex template """
        default_template = ""
        shader = self._construct_shader_from_data(vertex_data)

    def _parse_fragment_template(self, pass_id, fragment_data):
        """ Parses a fragment template """
        shader = self._construct_shader_from_data(fragment_data)

    def _construct_shader_from_data(self, data):
        """ Constructs a shader from a given dataset """
