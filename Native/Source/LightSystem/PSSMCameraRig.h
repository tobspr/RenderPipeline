#pragma once

#include "pandabase.h"
#include "luse.h"
#include "camera.h"
#include <vector>

class PSSMCameraRig {

    PUBLISHED:
        PSSMCameraRig(int num_cameras);
        ~PSSMCameraRig();

        void fit_to_camera(NodePath &cam_node, const LVecBase3f &light_vector);    

    protected:

        void init_cameras(int num_cameras);
        vector<PT(Camera)> _cameras;
};

