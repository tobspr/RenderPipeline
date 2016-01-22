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

#ifndef RP_INTERNAL_LIGHT_MANAGER_H
#define RP_INTERNAL_LIGHT_MANAGER_H

#include "referenceCount.h"
#include "RPLight.h"
#include "ShadowSource.h"
#include "ShadowAtlas.h"
#include "ShadowManager.h"
#include "PointerSlotStorage.h"
#include "GPUCommandList.h"

#define MAX_LIGHT_COUNT 65535
#define MAX_SHADOW_SOURCES 2048

NotifyCategoryDecl(lightmgr, EXPORT_CLASS, EXPORT_TEMPL);

/**
 * @brief Internal class used for handling lights and shadows.
 * @details This is the internal class used by the pipeline to handle all
 *   lights and shadows. It stores references to the lights, manages handling
 *   the light and shadow slots, and also communicates with the GPU with the
 *   GPUCommandQueue to store light and shadow source data.
 */
class InternalLightManager {

    PUBLISHED:
        InternalLightManager();

        void add_light(PT(RPLight) light);
        void remove_light(PT(RPLight) light);

        void update();
        
        inline int get_max_light_index() const;
        inline size_t get_num_lights() const;
        inline size_t get_num_shadow_sources() const;

        inline void set_command_list(GPUCommandList *cmd_list);
        inline void set_shadow_manager(ShadowManager* mgr);

    protected:
        
        void setup_shadows(RPLight* light);

        void gpu_update_light(RPLight* light);
        void gpu_update_source(ShadowSource* source);
        void gpu_remove_light(RPLight* light);
        void gpu_remove_consecutive_sources(ShadowSource *first_source, size_t num_sources);
 
        void update_lights();
        void update_shadow_sources();

        GPUCommandList* _cmd_list;
        ShadowManager* _shadow_manager;

        PointerSlotStorage<RPLight*, MAX_LIGHT_COUNT> _lights;
        PointerSlotStorage<ShadowSource*, MAX_SHADOW_SOURCES> _shadow_sources;

};

#include "InternalLightManager.I"

#endif // RP_INTERNAL_LIGHT_MANAGER_H
