
#ifndef RP_LIGHT_H
#define RP_LIGHT_H

#include "referenceCount.h"
#include "luse.h"
#include "GPUCommand.h"

class RPLight : public ReferenceCount {

    PUBLISHED:

        enum LightType {
            LT_point_light = 1,
            LT_spot_light = 2
        };

    public:
        RPLight(LightType light_type);
        ~RPLight();

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

    protected:
        
        bool _dirty;
        int _slot;
        LVecBase3f _position;
        LVecBase3f _color;
        LightType _light_type;


    public:
      static TypeHandle get_class_type() {
        return _type_handle;
      }
      static void init_type() {
        ReferenceCount::init_type();
        register_type(_type_handle, "RPLight", ReferenceCount::get_class_type());
      }
      virtual TypeHandle get_type() const {
        return get_class_type();
      }

    private:
      static TypeHandle _type_handle;

};

#include "RPLight.I"

#endif // RP_LIGHT_H