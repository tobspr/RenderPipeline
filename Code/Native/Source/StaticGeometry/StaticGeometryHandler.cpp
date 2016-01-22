/**
 * 
 * RenderPipeline
 * 
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */


#include "StaticGeometryHandler.h"

#include "datagram.h"
#include "datagramIterator.h"

#include "SGTriangleStrip.h"
#include "SGDataset.h"

#include "common.h"



StaticGeometryHandler::StaticGeometryHandler() {

    _dataset_tex = new Texture("DatasetStorage");
    _mapping_tex = new Texture("DatasetMappings");
    _indirect_tex = new Texture("SGIndirectTex");
    _drawn_objects_tex = new Texture("DrawnObjectsList");
    _dynamic_strips_tex = new Texture("DynamicStripList");
    _dataset_index = 0;
    _num_rendered_objects = 0;


    const int max_objects_per_frame = 128;
    const int max_strips_per_frame = 100000;

    // The dataset texture stores the data of all triangle strips. It can be quite
    // huge, however it does not have to get uploaded every frame.
    // We add +2 for the bounding volume, and +1 for the visibility flags to the x-size.
    // For the y size, we add 1 to store the number of strips in the first component.
    _dataset_tex->setup_2d_texture(SG_TRI_GROUP_SIZE * 3 * 2 + 2 + 1, SG_MAX_DATASET_STRIPS, Texture::T_float, Texture::F_rgba16);

    // The mapping tex assigns strips to a dataset. Right now a dataset can have
    // up to n strips, and we support up to 32 datasets
    _mapping_tex->setup_2d_texture(SG_MAX_DATASET_STRIPS, 32, Texture::T_int, Texture::F_r32i);

    // Store a texture which is used in the indirect draw call
    _indirect_tex->setup_buffer_texture(4, Texture::T_int, Texture::F_r32i, GeomEnums::UH_dynamic);

    // Store a list of rendered objects, for each object this stores
    // the object index, and its transform matrix.
    // We reserve 1 pixel to store the amount of drawn objects, and each object
    // takes 1 pixel for its id and 4 pixels for its transform matrix.
    // _drawn_objects_tex->setup_buffer_texture(1 + max_objects_per_frame * 5, Texture::T_float, Texture::F_rgba16, GeomEnums::UH_dynamic);
    _drawn_objects_tex->setup_2d_texture(1 + max_objects_per_frame * 5, 1, Texture::T_float, Texture::F_rgba32);

    // This texture is used to write all rendered strips to.
    // For each rendered strip, there is an object reference (to get the transform mat),
    // and a global strip reference.
    // For each strip we store a thread id and a strip id, so we multiply by 2
    _dynamic_strips_tex->setup_buffer_texture(max_strips_per_frame, Texture::T_int, Texture::F_rg32, GeomEnums::UH_static);
}


StaticGeometryHandler::~StaticGeometryHandler() {

    // TODO: Delete all datasets and their strips

}


DatasetReference StaticGeometryHandler::load_dataset(const Filename &src) {

    // TODO: Check for duplicates
    // for (DatasetList::const_iterator iter = _datasets.cbegin(); iter != _datasets.cend(); ++iter) {
    // }

    ifstream infile(src.get_fullpath(), ios::in | ios::binary | ios::ate);

    if (!infile.is_open()) {
        cout << "ERROR: Could not open " << src.get_fullpath() << "!" << endl;
        return -1;
    }

    // Extract filesize and reset filepointer afterwards
    size_t fsize = infile.tellg();
    infile.seekg(0, ios::beg);

    // Read file content
    char *data = new char[fsize];
    infile.read(data, fsize);

    // Construct datagram and an iterator from file content
    Datagram dg(data, fsize);
    DatagramIterator dgi(dg);

    // For now we assume the file is structured correctly, and the header is
    // correct aswell
    string header = dgi.get_fixed_string(4);
    size_t tri_group_size = dgi.get_uint32();

    if (tri_group_size != SG_TRI_GROUP_SIZE) {
        cout << "ERROR: The rpsg file uses a tri-group size of " << tri_group_size << ", but expected"
            << " a size of "<< SG_TRI_GROUP_SIZE << endl;
        cout << "Please regenerate the file!" << endl;
        delete [] data;
        return -1;    
    } 

    size_t num_strips = dgi.get_uint32();

    if (num_strips >= SG_MAX_DATASET_STRIPS) {
        cout << "ERROR! Dataset exceeds maximum amount of " << SG_MAX_DATASET_STRIPS << " strips (has " << num_strips << ")!" << endl;
        delete [] data;
        return -1;
    }

    SGDataset *dataset = new SGDataset();
    dataset->read_bounds(dgi);

    // Read in all strips and store them
    PTA_uchar dataset_handle = _dataset_tex->modify_ram_image();
    for (size_t i = 0; i < num_strips; ++i) {
        SGTriangleStrip* strip = new  SGTriangleStrip();
        strip->load_from_datagram(dgi);
        strip->write_to(dataset_handle, _dataset_index++);
        dataset->attach_strip(strip);
    }

    PTA_uchar mapping_handle = _mapping_tex->modify_ram_image();

    dataset->write_mappings(mapping_handle, _datasets.size());

    if (dgi.get_remaining_size() != 0) {
        cout << "Corrupt RPSG file! " << dgi.get_remaining_size() << " bytes left!" << endl;
    }

    // Write out debug textures?
    // _dataset_tex->write("dataset.png");
    // _mapping_tex->write("mappings.png");

    // Attach dataset, clean up the variables, and finally return a handle to the dataset
    _datasets.push_back(dataset);
    delete [] data;

    return _datasets.size() - 1;
}


SGDataset* StaticGeometryHandler::get_dataset(DatasetReference dataset) {
    if (dataset < 0 || dataset >= _datasets.size()) {
        cout << "ERROR: Could not find dataset with id " << dataset << endl;
        return NULL;        
    }
    return _datasets.at(dataset);
}


void StaticGeometryHandler::add_for_draw(DatasetReference dataset, const LMatrix4f &transform) {

    PTA_uchar handle = _drawn_objects_tex->modify_ram_image();
    float* f_handle = reinterpret_cast<float*>(handle.p());
    
    // Store the new amount of rendered objects
    f_handle[0] = _num_rendered_objects + 1;
    f_handle[1] = 0;
    f_handle[2] = 0;
    f_handle[3] = 0;

    int data_offset = 4 + _num_rendered_objects * 20;

    f_handle[data_offset++] = dataset; // Render object with ID n
    f_handle[data_offset++] = 0; // reserved
    f_handle[data_offset++] = 0; // reserved
    f_handle[data_offset++] = 0; // reserved

    for (LMatrix4f::iterator iter = transform.begin(); iter != transform.end(); ++iter) {
        f_handle[data_offset++] = (*iter);
    }

    _num_rendered_objects ++;

}


void StaticGeometryHandler::clear_render_list() {
    // cout << "rendered " << _num_rendered_objects << " objects " << endl;
    _num_rendered_objects = 0;
}


PT(Texture) StaticGeometryHandler::get_dataset_tex() {
    return _dataset_tex;
}

PT(Texture) StaticGeometryHandler::get_mapping_tex() {
    return _mapping_tex;
}


PT(Texture) StaticGeometryHandler::get_indirect_tex() {
    return _indirect_tex;
}


PT(Texture) StaticGeometryHandler::get_drawn_objects_tex() {
    return _drawn_objects_tex;
}


PT(Texture) StaticGeometryHandler::get_dynamic_strips_tex() {
    return _dynamic_strips_tex;
}

