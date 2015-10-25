
#include "StaticGeometryHandler.h"

#include "datagram.h"
#include "datagramIterator.h"

#include "SGTriangleStrip.h"
#include "SGDataset.h"



StaticGeometryHandler::StaticGeometryHandler() {

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

    // Read in all strips
    for (size_t i = 0; i < num_strips; ++i) {
        SGTriangleStrip* strip = new  SGTriangleStrip();
        strip->load_from_datagram(dgi);
        dataset->attach_strip(strip);
    }

    // Attach dataset, clean up the variables, and finally return a handle to the dataset
    _datasets.push_back(dataset);
    delete [] data;
    return _datasets.size() - 1;
}


SGDataset* StaticGeometryHandler::get_dataset(DatasetReference dataset) {
    return _datasets.at(dataset);
}


void StaticGeometryHandler::add_for_draw(DatasetReference dataset, const LMatrix4f &transform) {
    cout << "Adding dataset " << dataset << " for draw" << endl;
    cout << "\tMat = " << transform << endl;
}
