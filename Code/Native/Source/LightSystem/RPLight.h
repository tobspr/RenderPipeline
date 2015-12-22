
#ifndef RP_LIGHT_H
#define RP_LIGHT_H

#include "referenceCount.h"
#include "luse.h"
#include "GPUCommand.h"
#include "ShadowSource.h"

class RPLight : public ReferenceCount {

    PUBLISHED:
        enum LightType {
            LT_empty = 0,
            LT_point_light = 1,
            LT_spot_light = 2,
        };

    public:
        RPLight(LightType light_type);
        virtual ~RPLight();

        virtual void init_shadow_sources() = 0;
        virtual void update_shadow_sources() = 0;
        virtual void write_to_command(GPUCommand &cmd);
        
        inline int get_num_shadow_sources() const;
        inline ShadowSource* get_shadow_source(int index) const;

        inline void mark_dirty();
        inline void unset_dirty_flag();
        inline bool is_dirty() const;
        inline bool has_slot() const;
        inline void remove_slot();
        inline void assign_slot(int slot);

        inline void invalidate_shadows();

    PUBLISHED:

        inline void set_pos(const LVecBase3f &pos);
        inline void set_pos(float x, float y, float z);

        inline void set_color(const LVecBase3f &color);
        inline void set_color(float r, float g, float b);

        inline LightType get_light_type() const;

        inline void set_casts_shadows(bool flag = true);
        inline bool get_casts_shadows() const;

        inline int get_slot() const;
        inline void set_ies_profile(int profile);

    protected:
        
        bool _dirty;
        bool _casts_shadows;
        int _slot;
        int _ies_profile;
        LVecBase3f _position;
        LVecBase3f _color;
        LightType _light_type;

        vector<ShadowSource*> _shadow_sources;
};

#include "RPLight.I"

#endif // RP_LIGHT_H