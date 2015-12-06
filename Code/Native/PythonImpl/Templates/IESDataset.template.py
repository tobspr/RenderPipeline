
def __init__(self):
    self._vertical_angles = None
    self._horizontal_angles = None
    self._candela_values = None

def set_horizontal_angles(self, horizontal_angles):
    self._horizontal_angles = horizontal_angles

def set_vertical_angles(self, vertical_angles):
    self._vertical_angles = vertical_angles

def set_candela_values(self, candela_values):
    self._candela_values = candela_values

def get_candela_value_from_index(self, vertical_angle_idx, horizontal_angle_idx):
    index = vertical_angle_idx + horizontal_angle_idx * len(self._vertical_angles)
    return self._candela_values[index]


def get_candela_value(self, vertical_angle, horizontal_angle):

    # NOTICE: Since python is slower, we always only assume a dataset without
    # horizontal angles
    return self.get_vertical_candela_value(0, vertical_angle)


def get_vertical_candela_value(self, horizontal_angle_idx, vertical_angle):
    if vertical_angle < 0.0:
        return 0.0

    if vertical_angle > self._vertical_angles[ len(self._vertical_angles) - 1]:
        return 0.0


    for vertical_index in range(1, len(self._vertical_angles)):
        curr_angle = self._vertical_angles[vertical_index]

        if curr_angle > vertical_angle:
            prev_angle = self._vertical_angles[vertical_index - 1]
            prev_value = self.get_candela_value_from_index(vertical_index - 1, horizontal_angle_idx)
            curr_value = self.get_candela_value_from_index(vertical_index, horizontal_angle_idx)
            lerp = (vertical_angle - prev_angle) / (curr_angle - prev_angle)

            assert lerp >= 0.0 and lerp <= 1.0
            return curr_value * lerp + prev_value * (1.0 - lerp)

    return 0.0


def generate_dataset_texture_into(self, dest_tex, z, resolution_vertical, resolution_horizontal):

    dest = PNMImage(resolution_vertical, resolution_horizontal, 1, 65535)

    for vert in range(resolution_vertical):
        for horiz in range(resolution_horizontal):
            vert_angle = vert / (resolution_vertical-1.0) * 180.0
            horiz_angle = horiz / (resolution_horizontal-1.0) * 360.0
            candela = self.get_candela_value(vert_angle, horiz_angle)
            dest.set_xel(vert, horiz, candela)

    dest_tex.load(dest, z, 0)

