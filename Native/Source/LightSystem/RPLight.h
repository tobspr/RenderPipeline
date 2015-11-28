
#ifndef RP_LIGHT_H
#define RP_LIGHT_H

#include "referenceCount.h"
#include "luse.h"
#include "GPUCommand.h"

class RPLight : public ReferenceCount {

    PUBLISHED:

        enum LightType {
            LT_point_light = 1,
            LT_spot_light = 2,
        };

    public:
        RPLight(LightType light_type);
        virtual ~RPLight();

    PUBLISHED:

        virtual void write_to_command(GPUCommand &cmd);

        inline void mark_dirty();
        inline void unset_dirty_flag();
        inline bool is_dirty();
        inline void set_pos(const LVecBase3f &pos);
        inline void set_pos(float x, float y, float z);

        inline void set_color(const LVecBase3f &color);
        inline void set_color(float r, float g, float b);

        inline LightType get_light_type();

        inline bool has_slot();
        inline void remove_slot();
        inline void assign_slot(int slot);

        inline int get_slot();
        inline void set_ies_profile(int profile);

    protected:
        
        bool _dirty;
        int _slot;
        int _ies_profile;
        LVecBase3f _position;
        LVecBase3f _color;
        LightType _light_type;

};

#include "RPLight.I"

#endif // RP_LIGHT_H