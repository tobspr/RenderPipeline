#pragma once

#include "pandabase.h"
#include "pta_float.h"
#include "pointerToArray.h"
#include "texture.h"

NotifyCategoryDecl(iesdataset, EXPORT_CLASS, EXPORT_TEMPL);


/**
 * @brief This class generates a LUT from IES data.
 * @details This class is used by the IESLoader to generate a LUT texture which
 *   is used in the shaders to perform IES lighting. It takes a set of vertical
 *   and horizontal angles, as well as a set of candela values, which then are
 *   lineary interpolated onto a 2D LUT Texture.
 */
class IESDataset {

    PUBLISHED:
        IESDataset();
    
        void set_vertical_angles(const PTA_float &vertical_angles);
        void set_horizontal_angles(const PTA_float &horizontal_angles);
		void set_candela_values(const PTA_float &candela_values);
		
        void generate_dataset_texture_into(Texture* dest_tex, size_t z) const;

    public:

        float get_candela_value(float vertical_angle, float horizontal_angle) const;
		float get_candela_value_from_index(size_t vertical_angle_idx, size_t horizontal_angle_idx) const;
        float get_vertical_candela_value(size_t horizontal_angle_idx, float vertical_angle) const;

    private:
        PTA_float _vertical_angles;
        PTA_float _horizontal_angles;
        PTA_float _candela_values; 
};
