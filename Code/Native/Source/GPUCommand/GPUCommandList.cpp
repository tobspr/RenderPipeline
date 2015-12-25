#include "GPUCommandList.h"


/**
 * @brief Constructs a new GPUCommandList
 * @details This constructs a new GPUCommandList. By default, there are no commands
 *   in the list.
 */
GPUCommandList::GPUCommandList() {}

/**
 * @brief Pushes a GPUCommand to the command list. 
 * @details This adds a new GPUCommand to the list of commands to be processed.
 * 
 * @param cmd The command to add
 */
void GPUCommandList::add_command(const GPUCommand& cmd) {
    _commands.push(cmd);
}

/**
 * @brief Returns the number of commands in this list.
 * @details This returns the amount of commands which are currently stored in this
 *   list, and are waiting to get processed.
 * @return Amount of commands
 */
size_t GPUCommandList::get_num_commands() {
    return _commands.size();
}

/**
 * @brief Writes the first n-commands to a destination.
 * @details This takes the first #limit commands, and writes them to the
 *   destination using GPUCommand::write_to. See GPUCommand::write_to for
 *   further information about #dest. The limit controls after how much
 *   commands the processing will be stopped. All commands which got processed
 *   will get removed from the list.
 * 
 * @param dest Destination to write to, see GPUCommand::write_to
 * @param limit Maximum amount of commands to process
 * 
 * @return Amount of commands processed, between 0 and #limit.
 */
size_t GPUCommandList::write_commands_to(const PTA_uchar &dest, size_t limit) {
    size_t num_commands_written = 0;

    while (num_commands_written < limit && !_commands.empty()) {
        // Write the first command to the stream, and delete it afterwards
        _commands.front().write_to(dest, num_commands_written);
        _commands.pop();
        num_commands_written ++;
    }

    return num_commands_written;
}
