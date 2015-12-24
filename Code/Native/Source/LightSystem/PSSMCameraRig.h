#pragma once

#include "pandabase.h"
#include "luse.h"
#include "camera.h"
#include "nodePath.h"

#include <vector>


class PSSMCameraRig {

    PUBLISHED:
        PSSMCameraRig(size_t num_splits);
        ~PSSMCameraRig();

        void set_pssm_distance(float distance);
        void set_sun_distance(float distance);
        void set_use_fixed_film_size(bool flag);
        void set_use_tight_frustum(bool flag);
        void set_resolution(int resolution);
        void set_use_stable_csm(bool flag);
        void set_logarithmic_factor(float factor);
        
        void set_border_bias(float bias);

        void fit_to_camera(NodePath &cam_node, const LVecBase3f &light_vector);
        void reset_film_size_cache();

        NodePath get_camera(int index);

        void reparent_to(NodePath &parent);
        const PTA_LMatrix4f &get_mvp_array();
        const PTA_LVecBase2f &get_nearfar_array();

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
        float get_split_start(size_t split_index);
        LMatrix4f compute_mvp(int cam_index);
        LPoint3f get_interpolated_point(CoordinateOrigin origin, float depth);
        LPoint3f get_snap_offset(const LMatrix4f& mat, int resolution);

        vector<NodePath> _cam_nodes;
        vector<LVecBase2f> _max_film_sizes;

        // Current near and far points
        // Order: UL, UR, LL, LR (See CoordinateOrigin)
        LPoint3f _curr_near_points[4];
        LPoint3f _curr_far_points[4];
        float _pssm_distance;
        float _sun_distance;
        float _logarithmic_factor;
        float _border_bias;
        bool _use_fixed_film_size;
        bool _find_tight_frustum;
        bool _use_stable_csm;
        int _resolution;
        NodePath _parent;

        PTA_LMatrix4f _camera_mvps;
        PTA_LVecBase2f _camera_nearfar;

};

