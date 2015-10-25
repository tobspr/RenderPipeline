
#include "StaticGeometryHandler.h"

#include "datagram.h"
#include "datagramIterator.h"

#include "SGTriangleStrip.h"
#include "SGDataset.h"

#include "common.h"



StaticGeometryHandler::StaticGeometryHandler() {

    _dataset_tex = new Texture("DatasetStorage");
    _mapping_tex = new Texture("DatasetMappings");
    _dataset_index = 0;

    // Storage for 1024 strips should be enough for now
    _dataset_tex->setup_2d_texture(SG_TRI_GROUP_SIZE * 3, 1024, Texture::T_float, Texture::F_rgba32);


    // The mapping tex assigns strips to a dataset. Right now a dataset can have
    // up to 1024 strips, and we support up to 10 datasets
    _mapping_tex->setup_2d_texture(1024, 10, Texture::T_int, Texture::F_r32i);

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
    size_t num_strips = dgi.get_uint32();

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
    _dataset_tex->write("dataset.png");
    // _mapping_tex->write("mappings.png");

    // Attach dataset, clean up the variables, and finally return a handle to the dataset
    _datasets.push_back(dataset);
    delete [] data;

    return _datasets.size() - 1;
}


SGDataset* StaticGeometryHandler::get_dataset(DatasetReference dataset) {
    return _datasets.at(dataset);
}


void StaticGeometryHandler::add_for_draw(DatasetReference dataset, const LMatrix4f &transform) {
    _draw_list.clear();
    _draw_list.push_back(DrawEntry(dataset, transform));
}


void StaticGeometryHandler::on_scene_finish() {
    // Now actually draw all elements
}


PT(Texture) StaticGeometryHandler::get_dataset_tex() {
    return _dataset_tex;
}

PT(Texture) StaticGeometryHandler::get_mapping_tex() {
    return _mapping_tex;
}

