from __future__ import print_function

####### FIXME: Use debug objects ########
# from .DebugObject import DebugObject


import sys
sys.path.insert(0, "../")

from Native import *

import re
import math

from panda3d.core import PNMImage, PTAFloat, Texture
from direct.stdpy.file import open, isfile

class IESLoadException(Exception):
    pass


class IESProfileLoader():

    """ Loader class to load .IES files """

    PROFILES = [
        "IESNA91",
        "IESNA:LM-63-1995",
        "IESNA:LM-63-2002",
        "ERCO Leuchten GmbH  BY: ERCO/LUM650/8701",
        "ERCO Leuchten GmbH"
    ]

    KEYWORD_REGEX = re.compile("\[([A-Za-z0-8_-]+)\](.*)")

    def __init__(self):
        pass

    def load(self, pth):
        """ Loads a .ies file from a given directory """
        print("Loading ies profile from", pth)

        try:
            with open(pth, "r") as handle:
                lines = handle.readlines()
        except IOError as msg:
            print("Failed to open",pth,"->", msg)
            return None

        lines = [i.strip() for i in lines]

        # Parse version header
        self._check_version_header(lines.pop(0))

        # Parse arbitrary amount of keywords
        keywords = self._extract_keywords(lines)

        # Next line should be TILT=NONE according to the spec
        if lines.pop(0) != "TILT=NONE":
            raise IESLoadException("Expected TILT=NONE line, but none found!")

        # From now on, lines do not matter anymore, instead everything is
        # space seperated
        new_parts = (' '.join(lines)).replace(",", " ").split()
        read_int = lambda: int(new_parts.pop(0))
        read_float = lambda: float(new_parts.pop(0))

        # Amount of Lamps
        if read_int() != 1:
            raise IESLoadException("Only 1 Lamp supported!")

        # Extract various properties
        lumen_per_lamp = read_float()
        candela_multiplier = read_float()
        num_vertical_angles = read_int()
        num_horizontal_angles = read_int()

        if num_vertical_angles < 1 or num_horizontal_angles < 1:
            raise IESLoadException("Invalid of vertical/horizontal angles!")

        photometric_type = read_int()
        unit_type = read_int()

        # Check for a correct unit type, should be 1 for meters and 2 for feet
        if unit_type not in [1, 2]:
            raise IESLoadException("Invalid unit type")

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

        # Rescale values
        candela_values = [i / candela_scale for i in candela_values]

        if len(new_parts) != 0:
            print("Unhandled data at file-end left:", new_parts)


        print("Vertical angles range from", vertical_angles[0], "to", vertical_angles[-1])
        print("Horizontal angles range from", horizontal_angles[0], "to", horizontal_angles[-1])

        dataset = IESDataset()
        dataset.set_vertical_angles(self._list_to_pta(vertical_angles))
        dataset.set_horizontal_angles(self._list_to_pta(horizontal_angles))
        dataset.set_candela_values(self._list_to_pta(candela_values))

        """
        dest = PNMImage(360, 720, 3)
        for horiz_angle in range(720):
            for vert_angle in range(360):
                value = dataset.get_candela_value(vert_angle / 2.0, horiz_angle / 2.0)
                dest.set_xel(int(vert_angle), int(horiz_angle), value, value, value)

        dest.write("IESRaw.png")

        dest = PNMImage(256, 256)
        for x in range(256):
            for y in range(256):
                local_x = (x - 127.0) / 256.0
                local_y = (y - 127.0) / 256.0

                horiz_angle = math.atan2(local_y, local_x) / math.pi * 180.0
                if horiz_angle < 0:
                    horiz_angle += 360.0
                if horiz_angle > 360.0:
                    horiz_angle -= 360.0
                radius = math.sqrt(local_x * local_x + local_y * local_y) * 2.0
                value = dataset.get_candela_value(radius * 90.0, horiz_angle)
                dest.set_xel(x, y, value, value, value)
                # dest.set_xel(x, y, horiz_angle / 360.0, 0, 0)

        dest.write("IESRadius.png")
        """

        tex = Texture("temp")
        tex.setup_3d_texture(360, 720, 1, Texture.T_float, Texture.F_r16)

        dataset.generate_dataset_texture_into(tex, 0, 360, 720)

        tex.write("generated.png")

    def _list_to_pta(self, list_values):
        """ Converts a list to a PTAFloat """
        pta = PTAFloat.empty_array(len(list_values))
        for i, v in enumerate(list_values):
            pta[i] = v
        return pta

    def _check_version_header(self, first_line):
        """ Checks if the IES version header is correct and the specified IES
        version is supported """
        if first_line not in self.PROFILES:
            raise IESLoadException("Unsupported Profile: " + first_line)

    def _extract_keywords(self, lines):
        """ Extracts the keywords from a list of lines, and removes all lines
        containing keywords """
        keywords = {}
        while lines:
            line = lines.pop(0)
            if not line.startswith("["):

                # Special format used by some IES files, indicates end of properties
                # By just checking for the tilt keyword instead of validating each line,
                # we can read even malformed lines 
                if line != "TILT=NONE":
                    continue

                # No keyword, we popped the line already tho, so append it again
                lines.insert(0, line)
                return keywords
            else:

                match = self.KEYWORD_REGEX.match(line)
                if match:
                    key, val = match.group(1, 2)
                    keywords[key.strip()] = val.strip()
                else:
                    raise IESLoadException("Invalid keyword line: " + line)

        return keywords

if __name__ == "__main__":

    loader = IESProfileLoader()
    loader.load("../../Data/IESProfiles/MediumScatter.ies")
