
class GPUCommandList(object):
    
    def __init__(self):
        self._commands = []

    def add_command(self, cmd):
        self._commands.append(cmd)

    def get_num_commands(self):
        return len(self._commands)

    def write_commands_to(self, dest, limit=32):
        num_commands_written = 0

        while num_commands_written < limit and self._commands:
            self._commands.pop(0).write_to(dest, num_commands_written)
            num_commands_written += 1

        return num_commands_written
