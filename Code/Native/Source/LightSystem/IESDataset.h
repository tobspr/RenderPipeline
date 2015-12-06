#pragma once

#include "pandabase.h"
#include "pta_float.h"
#include "pointerToArray.h"
#include "texture.h"

class IESDataset {

    PUBLISHED:
        IESDataset();
        ~IESDataset();
    
        void set_vertical_angles(const PTA_float &vertical_angles);
        void set_horizontal_angles(const PTA_float &horizontal_angles);
		void set_candela_values(const PTA_float &candela_values);
		float get_candela_value(float vertical_angle, float horizontal_angle);
        void generate_dataset_texture_into(Texture* dest_tex, int z, int resolution_vertical, int resolution_horizontal);

    public:

		float get_candela_value_from_index(size_t vertical_angle_idx, size_t horizontal_angle_idx);
        float get_vertical_candela_value(size_t horizontal_angle_idx, float vertical_angle);

    private:
        
        PTA_float _vertical_angles;
        PTA_float _horizontal_angles;
        PTA_float _candela_values;

  
};


