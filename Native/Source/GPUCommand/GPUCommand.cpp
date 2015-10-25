
#include "GPUCommand.h"


#include <iostream>
#include <stdlib.h>



GPUCommand::GPUCommand(CommandType command_type) {
    _command_type = command_type;
    for (int i = 1; i < 32; i++) {
        _data[i] = 0.0;
    }
    _current_index = 1;
    _data[0] = (float)command_type;
}

GPUCommand::~GPUCommand() {

    
    
}

void GPUCommand::print_data() {
    cout << "GPUCommand(type=" << _command_type << ", size=" << _current_index << ")" << endl;
    cout << "Data: ";
    for (int k = 0; k < 32; k++) {
        cout << _data[k] << " ";
    }
    cout << endl;
}

void GPUCommand::write_to(const PTA_uchar &dest, size_t command_index) {
    size_t command_size = 32 * sizeof(float);
    size_t offset = command_index * command_size;
    memcpy(dest.p() + offset, &_data[0], command_size);
}
