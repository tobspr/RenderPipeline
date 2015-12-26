from __future__ import print_function

import re

from panda3d.core import PTAFloat
from direct.stdpy.file import open

from ..Native import IESDataset
from .DebugObject import DebugObject

class IESLoaderException(Exception):
    """ Exception which is thrown when an error occurs during loading an IES
    Profile """

class IESProfileLoader(DebugObject):

    """ Loader class to load .IES files and create an IESDataset from it """

    # Supported IES Profiles
    PROFILES = [
        "IESNA:LM-63-1986",
        "IESNA:LM-63-1991",
        "IESNA91",
        "IESNA:LM-63-1995",
        "IESNA:LM-63-2002",
        "ERCO Leuchten GmbH  BY: ERCO/LUM650/8701",
        "ERCO Leuchten GmbH"
    ]

    # Regexp for extracting keywords
    KEYWORD_REGEX = re.compile(r"\[([A-Za-z0-8_-]+)\](.*)")

    def __init__(self):
        DebugObject.__init__(self)

    def load(self, pth):
        """ Loads a .IES file from a given filename. """
        self.debug("Loading ies profile from", pth)

        try:
            with open(pth, "r") as handle:
                lines = handle.readlines()
        except IOError as msg:
            self.error("Failed to open", pth, ":", msg)
            return None

        lines = [i.strip() for i in lines]

        # Parse version header
        self._check_version_header(lines.pop(0))

        # Parse arbitrary amount of keywords
        keywords = self._extract_keywords(lines)

        # Next line should be TILT=NONE according to the spec
        if lines.pop(0) != "TILT=NONE":
            raise IESLoaderException("Expected TILT=NONE line, but none found!")

        # From now on, lines do not matter anymore, instead everything is
        # space seperated
        new_parts = (' '.join(lines)).replace(",", " ").split()
        read_int = lambda: int(new_parts.pop(0))
        read_float = lambda: float(new_parts.pop(0))

        # Amount of Lamps
        if read_int() != 1:
            raise IESLoaderException("Only 1 Lamp supported!")

        # Extract various properties
        lumen_per_lamp = read_float()
        candela_multiplier = read_float()
        num_vertical_angles = read_int()
        num_horizontal_angles = read_int()

        if num_vertical_angles < 1 or num_horizontal_angles < 1:
            raise IESLoaderException("Invalid of vertical/horizontal angles!")

        photometric_type = read_int()
        unit_type = read_int()

        # Check for a correct unit type, should be 1 for meters and 2 for feet
        if unit_type not in [1, 2]:
            raise IESLoaderException("Invalid unit type")

        width = read_float()
        length = read_float()
        height = read_float()
        ballast_factor = read_float()
        future_use = read_float() # Unused field for future usage
        input_watts = read_float()

        # Read vertical angles
        vertical_angles = [read_float() for i in range(num_vertical_angles)]
        horizontal_angles = [read_float() for i in range(num_horizontal_angles)]

        candela_values = []
        candela_scale = 0.0

        for i in range(num_horizontal_angles):
            vertical_data = [read_float() for i in range(num_vertical_angles)]
            candela_scale = max(candela_scale, max(vertical_data))
            candela_values += vertical_data

        # Rescale values, divide by maximum
        candela_values = [i / candela_scale for i in candela_values]

        if len(new_parts) != 0:
            self.warn("Unhandled data at file-end left:", new_parts)

            # Dont abort here, some formats like those from ERCO Leuchten GmbH
            # have an END keyword, just ignore everything after the data was
            # read in.

        dataset = IESDataset()
        dataset.set_vertical_angles(self._list_to_pta(vertical_angles))
        dataset.set_horizontal_angles(self._list_to_pta(horizontal_angles))
        dataset.set_candela_values(self._list_to_pta(candela_values))

        # Testing code to write out the LUT
        if False:
            # from panda3d.core import Texture
            # tex = Texture("temp")
            # tex.setup_3d_texture(512, 512, 1, Texture.T_float, Texture.F_r16)
            # dataset.generate_dataset_texture_into(tex, 0)
            # tex.write("generated.png")

        return dataset

    def _list_to_pta(self, list_values):
        """ Converts a list to a PTAFloat """
        pta = PTAFloat.empty_array(len(list_values))
        for i, val in enumerate(list_values):
            pta[i] = val
        return pta

    def _check_version_header(self, first_line):
        """ Checks if the IES version header is correct and the specified IES
        version is supported """
        if first_line not in self.PROFILES:
            raise IESLoaderException("Unsupported Profile: " + first_line)

    def _extract_keywords(self, lines):
        """ Extracts the keywords from a list of lines, and removes all lines
        containing keywords """
        keywords = {}
        while lines:
            line = lines.pop(0)
            if not line.startswith("["):

                # Special format used by some IES files, indicates end of properties
                # By just checking for the tilt keyword instead of validating each line,
                # we can read even malformed lines, like those from ERCO Leuchten GmbH
                if line != "TILT=NONE":
                    continue

                # No keyword, we popped the line already tho, so append it again
                lines.insert(0, line)
                return keywords
            else:

                # Try matching the keywords
                match = self.KEYWORD_REGEX.match(line)
                if match:
                    key, val = match.group(1, 2)
                    keywords[key.strip()] = val.strip()
                else:
                    raise IESLoaderException("Invalid keyword line: " + line)

        return keywords
