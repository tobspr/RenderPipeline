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

        PT(Texture) get_dataset_tex();
        PT(Texture) get_mapping_tex();
        PT(Texture) get_indirect_tex();
        PT(Texture) get_drawn_objects_tex();
        PT(Texture) get_dynamic_strips_tex();

        void clear_render_list();

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



        PT(Texture) _dataset_tex;
        PT(Texture) _mapping_tex;
        PT(Texture) _indirect_tex;
        PT(Texture) _drawn_objects_tex;
        PT(Texture) _dynamic_strips_tex;

        int _dataset_index;
        int _num_rendered_objects;
};

