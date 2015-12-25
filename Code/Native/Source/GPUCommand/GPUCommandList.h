#ifndef RP_GPU_COMMAND_LIST_H
#define RP_GPU_COMMAND_LIST_H

#include "pandabase.h"
#include "GPUCommand.h"

#include <queue>

/**
 * @brief Class to store a list of commands.
 * @details This is a class to store a list of GPUCommands. It provides
 *   functionality to only provide the a given amount of commands at one time. 
 */
class GPUCommandList {

    PUBLISHED:
        GPUCommandList();

        void add_command(const GPUCommand& cmd);
        size_t get_num_commands();
        size_t write_commands_to(const PTA_uchar &dest, size_t limit = 32);

    protected:

        queue<GPUCommand> _commands;
};

#endif // RP_GPU_COMMAND_LIST_H
