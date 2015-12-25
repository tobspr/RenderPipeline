
def __init__(self):
    self._max_lights = 65000
    self._lights = [None] * self._max_lights
    self._max_light_index = 0
    self._num_stored_lights = 0
    self._cmd_list = None

def set_command_list(self, cmd_list):
    self._cmd_list = cmd_list

def get_max_light_index(self):
    return self._max_light_index

def add_light(self, light):

    if light.has_slot():
        print("ERROR: Cannot add light since it already has a slot!")
        return

    try:
        slot = self._lights.index(None)
    except ValueError:
        print("ERROR: All light slots used!")
        return

    self._num_stored_lights += 1
    self._max_light_index = max(self._max_light_index, slot)

    self._lights[slot] = light
    light.assign_slot(slot)
    light.unset_dirty_flag()

    cmd_add = GPUCommand(GPUCommand.CMD_store_light)
    light.write_to_command(cmd_add)
    self._cmd_list.add_command(cmd_add)

def remove_light(self, light):
    if not light.has_slot():
        print("ERROR: Cannot detach light, light has no slot!")
        return

    self._lights[light.get_slot()] = None

    cmd_remove = GPUCommand(GPUCommand.CMD_remove_light)
    cmd_remove.push_int(light.get_slot())
    self._num_stored_lights -= 1

    if light.get_slot() == self._max_light_index:
        curr = self._max_light_index
        while _lights[curr] is None:
            curr -= 1
        self._max_light_index = curr

    light.remove_slot()

def get_num_stored_lights(self):
    return self._num_stored_lights

def update(self):
    for k in range(self._max_light_index + 1):
        if self._lights[k] is not None and self._lights[k].is_dirty():
            cmd_update = GPUCommand(GPUCommand.CMD_store_light)
            self._lights[k].write_to_command(cmd_update)
            self._lights[k].unset_dirty_flag()
            self._cmd_list.add_command(cmd_update)
