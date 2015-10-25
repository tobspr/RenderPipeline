#pragma once

#include "pandabase.h"
#include "filename.h"

#include "StaticGeometry.h"


typedef int DatasetReference;

class StaticGeometryHandler {

    PUBLISHED:

        StaticGeometryHandler();
        ~StaticGeometryHandler();


        DatasetReference load_dataset(const Filename &src);


    private:

        typedef vector<SGDataset*> DatasetList;
        DatasetList _datasets;

};

