#pragma once

#include "pandabase.h"
#include "luse.h"
#include "filename.h"
#include "texture.h"
#include "renderState.h"

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

        PT(Texture) get_dataset_tex();
        PT(Texture) get_mapping_tex();

    private:

        typedef vector<SGDataset*> DatasetList;
        DatasetList _datasets;

        struct DrawEntry {
            DatasetReference dataset;
            LMatrix4f transform;

            DrawEntry(DatasetReference c_dataset, const LMatrix4f &c_transform) {
                dataset = c_dataset;
                transform = c_transform;
            }

        };

        typedef vector<DrawEntry> DrawList;
        DrawList _draw_list;

        PT(Texture) _dataset_tex;
        PT(Texture) _mapping_tex; 
        int _dataset_index;
};

