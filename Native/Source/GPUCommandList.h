 
#ifndef RP_COMMAND_LIST_H
#define RP_COMMAND_LIST_H

#include <pandabase.h>
#include <list>
#include "GPUCommand.h"


class GPUCommandList {

    PUBLISHED:
        GPUCommandList();
        ~GPUCommandList();

        void add_command(GPUCommand cmd);
        int write_commands_to(const PTA_uchar &dest, int limit = 32);

    protected:

        list<GPUCommand> _commands;
};



#endif // RP_COMMAND_LIST_H
