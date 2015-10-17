#pragma once


#include "dtool_config.h"
#include "pandabase.h"
#include "luse.h"

#include <vector>

class GPUCommand {

    PUBLISHED:

        enum CommandType {
            CMD_store_light = 1
        };

        GPUCommand(CommandType command_type);
        ~GPUCommand();


        inline size_t get_data_size();
        void enforce_width(size_t width, float fill_value=0.0);

        inline void push_int(int v);
        inline void push_float(float v);
        inline void push_vec3(const LVecBase3f &v);
        inline void push_vec4(const LVecBase4f &v);
        inline void push_mat4(const LMatrix4f &v);

        void write_to(const PTA_uchar &dest, size_t command_index);


        void print_data();

    private:
        CommandType _command_type;
        vector<float> _data;
};


#include "GPUCommand.I"