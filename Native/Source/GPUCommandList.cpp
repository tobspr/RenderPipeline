

#include "GPUCommandList.h"


GPUCommandList::GPUCommandList() {

}


GPUCommandList::~GPUCommandList() {
    // TODO: Implement me
}


void GPUCommandList::add_command(GPUCommand cmd) {
    _commands.push_back(cmd);
}

int GPUCommandList::get_num_commands() {
    return _commands.size();
}

int GPUCommandList::write_commands_to(const PTA_uchar &dest, int limit) {
    int num_commands_written = 0;

    while (num_commands_written < limit && !_commands.empty()) {
        // Write the first command to the stream, and delete it afterwards
        _commands.front().write_to(dest, num_commands_written);
        _commands.pop_front();
        num_commands_written ++;
    }

    return num_commands_written;
}
