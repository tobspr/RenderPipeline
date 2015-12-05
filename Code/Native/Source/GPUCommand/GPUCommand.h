
#ifndef RP_GPU_COMMAND_H
#define RP_GPU_COMMAND_H


#include "pandabase.h"
#include "luse.h"

class GPUCommand {

    PUBLISHED:

        enum CommandType {
            CMD_invalid = 0,
            CMD_store_light = 1,
            CMD_remove_light = 2
        };

        GPUCommand(CommandType command_type);
        ~GPUCommand();

        inline void push_int(int v);
        inline void push_float(float v);
        inline void push_vec3(const LVecBase3f &v);
        inline void push_vec4(const LVecBase4f &v);
        inline void push_mat4(const LMatrix4f &v);

        void write_to(const PTA_uchar &dest, size_t command_index);

        void print_data();

    private:
        CommandType _command_type;
        int _current_index;
        float _data[32];
};


#include "GPUCommand.I"

#endif // RP_GPU_COMMAND_H