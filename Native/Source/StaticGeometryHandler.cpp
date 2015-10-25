
#include "StaticGeometryHandler.h"

#include "datagram.h"
#include "datagramIterator.h"



StaticGeometryHandler::StaticGeometryHandler() {

}


StaticGeometryHandler::~StaticGeometryHandler() {

}


DatasetReference StaticGeometryHandler::load_dataset(const Filename &src) {

    // Check for duplicates
    // for (DatasetList::const_iterator iter = _datasets.cbegin(); iter != _datasets.cend(); ++iter) {
    // }

    ifstream infile(src.get_fullpath(), ios::in | ios::binary | ios::ate);


    if (!infile.is_open()) {
        cout << "ERROR: Could not open " << src.get_fullpath() << "!" << endl;
        return -1;
    }

    // Extract filesize
    size_t fsize = infile.tellg();

    // Reset filepointer to the beginning
    infile.seekg(0, ios::beg);

    // Read file content
    char *data = new char[fsize];
    infile.read(data, fsize);
    cout << "Read " << fsize << " bytes" << endl;

    // Construct datagram and an iterator from file content
    Datagram dg(data, fsize);
    DatagramIterator dgi(dg);

    // For now we assume the file is structured correctly, and the header is
    // correct aswell
    string header = dgi.get_fixed_string(4);

    cout << "Header: " << header << endl;

    size_t num_strips = dgi.get_uint32();
    cout << "Num strips: " << num_strips << endl;

    SGDataset *dataset = new SGDataset();

    // Read all strips
    for (size_t i = 0; i < num_strips; ++i) {

        SGTriangleStrip* strip = new  SGTriangleStrip();
        strip->load_from_datagram(dgi);
        dataset->attach_strip(strip);
    }

    _datasets.push_back(dataset);
    
    delete [] data;

    return _datasets.size() - 1;
}
