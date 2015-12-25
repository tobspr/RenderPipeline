#ifndef RP_GPU_COMMAND_H
#define RP_GPU_COMMAND_H

#include "pandabase.h"
#include "luse.h"

NotifyCategoryDecl(gpucommand, EXPORT_CLASS, EXPORT_TEMPL);

#define GPU_COMMAND_ENTRIES 32

/**
 * @brief Class for storing data to be transferred to the GPU.
 * @details This class can be seen like a packet, to be transferred to the GPU.
 *   It has a command type, which tells the GPU what to do once it recieved this
 *   "packet". It stores a limited amount of floating point components. 
 */
class GPUCommand {

    PUBLISHED:

        /**
         * The different types of GPUCommands. Each type has a special case in
         * the command queue processor. When adding new types, those need to
         * be handled in the command target, too.
         */
        enum CommandType {
            CMD_invalid = 0,
            CMD_store_light = 1,
            CMD_remove_light = 2,
            CMD_store_source = 3,
            CMD_remove_source = 4,
        };

        GPUCommand(CommandType command_type);
        
        inline void push_int(int v);
        inline void push_float(float v);
        inline void push_vec3(const LVecBase3f &v);
        inline void push_vec3(const LVecBase3i &v);
        inline void push_vec4(const LVecBase4f &v);
        inline void push_vec4(const LVecBase4i &v);
        inline void push_mat3(const LMatrix3f &v);
        inline void push_mat4(const LMatrix4f &v);

        void write_to(const PTA_uchar &dest, size_t command_index);
        void print_data();

    private:

        inline float convert_int_to_float(int v) const;

        CommandType _command_type;
        size_t _current_index;
        float _data[GPU_COMMAND_ENTRIES];
};

#include "GPUCommand.I"

#endif // RP_GPU_COMMAND_H
