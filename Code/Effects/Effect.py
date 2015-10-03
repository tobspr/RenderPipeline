

import copy

from External.PyYAML import yaml

class Effect:

    _DefaultOptions = {

    }

    _Passes = ["GBuffer", "Shadows", "Voxelize"]

    @classmethod
    def _generateHash(cls, filename, options):
        """ Generates an unique hash based on the effect path and options """
        # TODO: Implement me
        return 1

    def __init__(self):
        """ Constructs a new empty effect """
        self.options = copy.deepcopy(self._DefaultOptions)
        self.source = ""

    def setOptions(self, options):
        """ Sets the effect options, overriding the default options """
        for key, val in options.iteritems():
            if key not in self.options:
                print "ERROR: Unkown option:", key
                continue
            self.options[key] = val

    def load(self, filename):
        """ Loads the effect from the given filename """
        self.source = filename
        parsed_yaml = None

        # Get file content and parse it
        try:
            with open(filename, "r") as handle:
                parsed_yaml = yaml.load(handle)
        except IOError, msg:
            print "Could not find file:",filename,"!"
            print msg
            return False
        except yaml.YAMLError, msg:
            print "Could not parse file:",filename,"!"
            print msg
            return False

        self._parseContent(parsed_yaml)

    def _parseContent(self, parsed_yaml):
        """ Internal method to construct the effect from a parsed yaml object """

        for key, val in parsed_yaml.iteritems():
            if key == "Vertex":
                self._parseVertexTemplate(val)
            elif key.startswith("Fragment."):
                keyPass = key.replace("Fragment.", "")
                if keyPass in self._Passes:
                    self._parseFragmentTemplate(keyPass, val)
                else:
                    print "Error: Unrecognized pass:", keyPass
            else:
                print "Error: Unrecognized section:", key

    def _parseVertexTemplate(self, vertex_data):
        """ Parses a vertex template """
        default_template = ""
        shader = self._constructShaderFromData(vertex_data)

    def _parseFragmentTemplate(self, passId, fragment_data):
        """ Parses a fragment template """
        shader = self._constructShaderFromData(fragment_data)

    def _constructShaderFromData(self, data):
        """ Constructs a shader from a given dataset """
