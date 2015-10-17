
#include "GPUCommand.h"


#include <iostream>
#include <stdlib.h>



GPUCommand::GPUCommand(CommandType command_type) {
    _command_type = command_type;
    _data.push_back((float)command_type);
}

GPUCommand::~GPUCommand() {
}


void GPUCommand::enforce_width(size_t width, float fill_value) {
    if (_data.size() > width) {
        cerr << "enforce_width: command exceeds width!" << endl;
        return;
    }

    _data.resize(width, fill_value);
}


void GPUCommand::print_data() {
    cout << "GPUCommand(type=" << _command_type << ", size=" << _data.size() << ")" << endl;
    cout << "Data: ";
    for (int k = 0; k < _data.size(); k++) {
        cout << _data[k] << " ";
    }
    cout << endl;
}

void GPUCommand::write_to(const PTA_uchar &dest, size_t command_index) {
    size_t command_size = 32 * sizeof(float);
    size_t offset = command_index * command_size;
    memcpy(dest.p() + offset, &_data[0], command_size);
}
