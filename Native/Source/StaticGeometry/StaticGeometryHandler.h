#pragma once

#include "pandabase.h"
#include "luse.h"
#include "filename.h"
#include "texture.h"

class SGDataset;


typedef int DatasetReference;

class StaticGeometryHandler {

    PUBLISHED:

        StaticGeometryHandler();
        ~StaticGeometryHandler();

        DatasetReference load_dataset(const Filename &src);

    public:

        SGDataset* get_dataset(DatasetReference dataset);
        void add_for_draw(DatasetReference dataset, const LMatrix4f &transform);
        void on_scene_finish();

    private:

        typedef vector<SGDataset*> DatasetList;
        DatasetList _datasets;

        PT(Texture) _dataset_tex;
        PT(Texture) _mapping_tex; 
        int _dataset_index;
};

