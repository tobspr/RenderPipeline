
#include "PSSMCameraRig.h"

#include "orthographicLens.h"


PSSMCameraRig::PSSMCameraRig(size_t num_splits) {
    _pssm_distance = 100.0;
    _sun_distance = 200.0;
    init_cam_nodes(num_splits);
}

PSSMCameraRig::~PSSMCameraRig() {

}


void PSSMCameraRig::set_pssm_distance(float distance) {
    nassertv(distance > 1.0 && distance < 100000.0);
    _pssm_distance = distance;
}


void PSSMCameraRig::set_sun_distance(float distance) {
    nassertv(distance > 1.0 && distance < 100000.0);
    _sun_distance = distance;
}


void PSSMCameraRig::init_cam_nodes(size_t num_splits) {
    nassertv(num_splits > 0 && num_splits < 10);

    _cam_nodes.reserve(num_splits);
    for (size_t i = 0; i < num_splits; ++i)
    {
        Lens *lens = new OrthographicLens();
        lens->set_film_size(1, 1);
        lens->set_near_far(1, 1000);
        PT(Camera) cam = new Camera("pssm-cam" + to_string(i), lens);
        _cam_nodes.push_back(NodePath(cam));

    }
}


void PSSMCameraRig::reparent_to(NodePath &parent) {
    nassertv(_cam_nodes.size() > 0);
    for (size_t i = 0; i < _cam_nodes.size(); ++i) {
        _cam_nodes[i].reparent_to(parent);
    }
    _parent = parent;
}


float get_split_start(size_t split_index, size_t max_splits) {
    // Use a linear split scheme for now
    return (float)split_index / (float)max_splits;
}


LPoint3f PSSMCameraRig::get_interpolated_point(CoordinateOrigin origin, float depth) {
    nassertr(depth >= 0.0 && depth <= 1.0, NULL);  
    return _curr_near_points[origin] * (1.0 - depth) + _curr_far_points[origin] * depth;   
}


void PSSMCameraRig::compute_pssm_splits(const LMatrix4f& transform, float max_distance, const LVecBase3f& light_vector) {
    nassertv(!_parent.is_empty());

    // PSSM Distance should be smaller than camera far plane.
    nassertv(max_distance <= 1.0);

    // Compute the positions of all cameras
    for (size_t i = 0; i < _cam_nodes.size(); ++i) {
        float split_start = get_split_start(i, _cam_nodes.size()) * max_distance;
        float split_end = get_split_start(i + 1, _cam_nodes.size()) * max_distance;


        LVecBase3f start_points[4];
        LVecBase3f end_points[4];

        // Get split bounding box
        for (size_t k = 0; k < 4; ++k) {
            start_points[k] = get_interpolated_point((CoordinateOrigin)k, split_start);
            end_points[k] = get_interpolated_point((CoordinateOrigin)k, split_end);
        }

        // Compute approx. split mid point 
        LPoint3f split_mid = (start_points[UpperLeft] + end_points[LowerRight]) / 2.0;
        LPoint3f cam_start = split_mid + light_vector * _sun_distance; 

        // Find a good initial position
        _cam_nodes[i].set_pos(cam_start);
        _cam_nodes[i].look_at(split_mid);

        // Also reset the film size, offset and far-plane
        Camera* cam = DCAST(Camera, _cam_nodes[i].node());
        cam->get_lens()->set_film_size(1, 1);
        cam->get_lens()->set_film_offset(0, 0);
        cam->get_lens()->set_near_far(1, 100);

        // Collect all points which define the frustum
        LVecBase3f proj_points[8];
        LPoint2f screen_points[8];
        for (size_t k = 0; k < 4; ++k) {
            proj_points[k] = start_points[k];
            proj_points[k+4] = end_points[k];
        }

        // Find minimum and maximum extends of the points
        LVecBase3f min_extent(100000.0);
        LVecBase3f max_extent(-100000.0);

        LMatrix4f merged_transform = _parent.get_transform(_cam_nodes[i])->get_mat();

        // Now project all points to the screen space of the current camera and also
        // find the minimum and maximum extents
        for (size_t k = 0; k < 8; ++k) {
            LVecBase4f point(proj_points[k], 1);
            LPoint4f proj_point = merged_transform.xform(point);
            LPoint3f proj_point_3d(proj_point.get_x(), proj_point.get_y(), proj_point.get_z());
            cam->get_lens()->project(proj_point_3d, screen_points[k]);

            // Find min / max extents
            if (screen_points[k].get_x() > max_extent.get_x()) max_extent.set_x(screen_points[k].get_x());
            if (screen_points[k].get_y() > max_extent.get_y()) max_extent.set_y(screen_points[k].get_y());
            
            if (screen_points[k].get_x() < max_extent.get_x()) max_extent.set_x(screen_points[k].get_x());
            if (screen_points[k].get_y() < max_extent.get_y()) max_extent.set_y(screen_points[k].get_y());

            // cout << "projected " << point << " to " << proj_point << "(" << proj_point.get_y() << ")" << endl;
            if (proj_point.get_y() > max_extent.get_z()) max_extent.set_z(proj_point.get_y());
            if (proj_point.get_y() < min_extent.get_z()) min_extent.set_z(proj_point.get_y());
        }


        cout << "Z-Min / Z-Max = " << min_extent.get_z()  << " / " << max_extent.get_z() << endl;
        cam->get_lens()->set_near_far(1, max_extent.get_z());

        cam->show_frustum();
    }
}


void PSSMCameraRig::fit_to_camera(NodePath &cam_node, const LVecBase3f &light_vector) {
    nassertv(!cam_node.is_empty());

    // Get camera node transform
    const LMatrix4f &transform = cam_node.get_transform()->get_mat();

    // Get Camera and Lens pointers
    Camera* cam = DCAST(Camera, cam_node.get_child(0).node());
    nassertv(cam != NULL);
    Lens* lens = cam->get_lens();

    // Extract near and far points:
    // Extract Upper Left
    LPoint2f point(-1, 1);
    lens->extrude(point, _curr_near_points[UpperLeft], _curr_far_points[UpperLeft]);

    // Extract Upper Right
    point.set(1, 1);
    lens->extrude(point, _curr_near_points[UpperRight], _curr_far_points[UpperRight]);

    // Extract Lower Left
    point.set(-1, -1);
    lens->extrude(point, _curr_near_points[LowerLeft], _curr_far_points[LowerLeft]);

    // Extract Lower Right
    point.set(1, -1);
    lens->extrude(point, _curr_near_points[LowerRight], _curr_far_points[LowerRight]);

    // Construct MVP to project points to world space
    LMatrix4f mvp = transform * lens->get_view_mat();

    // Project all points to world space
    for (size_t i = 0; i < 4; ++i) {
        LPoint4f ws_near = mvp.xform(_curr_near_points[i]);
        LPoint4f ws_far = mvp.xform(_curr_far_points[i]);
        _curr_near_points[i].set(ws_near.get_x(), ws_near.get_y(), ws_near.get_z());
        _curr_far_points[i].set(ws_far.get_x(), ws_far.get_y(), ws_far.get_z());
    }

    // Do the actual PSSM
    compute_pssm_splits( transform, _pssm_distance / lens->get_far(), light_vector );
}

