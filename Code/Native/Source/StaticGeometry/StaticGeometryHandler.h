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

