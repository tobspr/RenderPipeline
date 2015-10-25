#pragma once

#include "pandabase.h"
#include "luse.h"
#include "filename.h"

class SGDataset;


typedef int DatasetReference;

class StaticGeometryHandler {

    PUBLISHED:

        StaticGeometryHandler();
        ~StaticGeometryHandler();

        DatasetReference load_dataset(const Filename &src);

        SGDataset* get_dataset(DatasetReference dataset);

        void add_for_draw(DatasetReference dataset, const LMatrix4f &transform);

    private:

        typedef vector<SGDataset*> DatasetList;
        DatasetList _datasets;

};

