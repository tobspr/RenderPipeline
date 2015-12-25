#ifndef RP_PSSM_HELPER_H
#define RP_PSSM_HELPER_H

#include "pandabase.h"
#include "luse.h"

/**
 * @brief Class to generate projection matrices.
 */
class PSSMHelper {

    PUBLISHED:
        static LMatrix4f find_projection_mat(
            const LVector4f &near_ul,
            const LVector4f &near_ur,
            const LVector4f &near_ll,
            const LVector4f &near_lr,
    
            const LVector4f &far_ul,
            const LVector4f &far_ur,
            const LVector4f &far_ll,
            const LVector4f &far_lr);

};

#endif // RP_PSSM_HELPER_H
