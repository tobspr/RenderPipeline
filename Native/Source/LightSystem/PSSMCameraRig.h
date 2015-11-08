#pragma once

#include "pandabase.h"
#include "luse.h"
#include "camera.h"
#include "nodePath.h"
#include <vector>


#define MAX_PSSM_SPLITS 10

class PSSMCameraRig {

    PUBLISHED:
        PSSMCameraRig(size_t num_splits);
        ~PSSMCameraRig();

        void set_pssm_distance(float distance);
        void set_sun_distance(float distance);
        void fit_to_camera(NodePath &cam_node, const LVecBase3f &light_vector);    

        NodePath get_camera(int index);

        void reparent_to(NodePath &parent);
        const PTA_LMatrix4f &get_mvp_array();

    public:

        // Used to access the near and far points in the array
        enum CoordinateOrigin {
            UpperLeft = 0,
            UpperRight,
            LowerLeft,
            LowerRight
        };

    protected:

        void init_cam_nodes(size_t num_splits);
        void compute_pssm_splits(const LMatrix4f& transform, float max_distance, const LVecBase3f &light_vector);
        LPoint3f get_interpolated_point(CoordinateOrigin origin, float depth);

        vector<NodePath> _cam_nodes;

        // Current near and far points
        // Order: UL, UR, LL, LR (See CoordinateOrigin)
        LPoint3f _curr_near_points[4];
        LPoint3f _curr_far_points[4];
        float _pssm_distance;
        float _sun_distance;
        NodePath _parent;

        PTA_LMatrix4f _camera_mvps;

};

