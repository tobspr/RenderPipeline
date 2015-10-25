#pragma once

#include "pandabase.h"
#include "filename.h"

#include "SGDataset.h"



typedef int DatasetReference;

class StaticGeometryHandler {

    PUBLISHED:

        StaticGeometryHandler();
        ~StaticGeometryHandler();

        DatasetReference load_dataset(const Filename &src);

        SGDataset* get_dataset(DatasetReference dataset);

    private:

        typedef vector<SGDataset*> DatasetList;
        DatasetList _datasets;

};

