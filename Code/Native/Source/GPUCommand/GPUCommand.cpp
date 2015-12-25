#include "GPUCommand.h"

#include <iostream>
#include <stdlib.h>


NotifyCategoryDef(GPUCommand, "RP");

/**
 * @brief Constructs a new GPUCommand with the given command type.
 * @details This will construct a new GPUCommand of the given command type.
 *   The command type should be of GPUCommand::CommandType, and determines
 *   what data the GPUCommand contains, and how it will be handled.
 * 
 * @param command_type The type of the GPUCommand
 */
GPUCommand::GPUCommand(CommandType command_type) {
    _command_type = command_type;
    _current_index = 0;
    memset(_data, 0x0, sizeof(float) * GPU_COMMAND_ENTRIES);

    // Store the command type as the first entry
    push_int(command_type);
}

/**
 * @brief Prints out the GPUCommand to the console
 * @details This method prints the type, size, and data of the GPUCommand to the
 *   console. This helps for debugging the contents of the GPUCommand. Keep
 *   in mind that integers might be shown in their binary float representation,
 *   depending on the setting in the GPUCommand::convert_int_to_float method.
 */
void GPUCommand::print_data() {
    cout << "GPUCommand(type=" << _command_type << ", size=" << _current_index << ")" << endl;
    cout << "Data = { ";
    for (int k = 0; k < GPU_COMMAND_ENTRIES; ++k) {
        cout << _data[k] << " ";
    }
    cout << "}" << endl;
}

/**
 * @brief Writes the GPU command to a given target.
 * @details This method writes all the data of the GPU command to a given target.
 *   The target should be a pointer to memory being big enough to hold the
 *   data. Presumably #dest will be a handle to texture memory.
 *   The command_index controls the offset where the data will be written
 *   to.
 *          
 * @param dest Handle to the memory to write the command to
 * @param command_index Offset to write the command to. The command will write
 *   its data to command_index * GPU_COMMAND_ENTRIES. When writing
 *   the GPUCommand in a GPUCommandList, the command_index will
 *   most likely be the index of the command in the list.
 */
void GPUCommand::write_to(const PTA_uchar &dest, size_t command_index) {
    size_t command_size = GPU_COMMAND_ENTRIES * sizeof(float);
    size_t offset = command_index * command_size;
    memcpy(dest.p() + offset, &_data, command_size);
}
