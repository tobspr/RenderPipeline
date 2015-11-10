
#include "PSSMCameraRig.h"

#include <cmath>
#include "orthographicLens.h"


PSSMCameraRig::PSSMCameraRig(size_t num_splits) {
    nassertv(num_splits > 0 && num_splits <= MAX_PSSM_SPLITS);
    _pssm_distance = 100.0;
    _sun_distance = 500.0;
    _use_fixed_film_size = false;
    _find_tight_frustum = true;
    _resolution = 512;
    _camera_mvps = PTA_LMatrix4f::empty_array(num_splits);
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
    _cam_nodes.reserve(num_splits);
    for (size_t i = 0; i < num_splits; ++i)
    {
        Lens *lens = new OrthographicLens();
        lens->set_film_size(1, 1);
        lens->set_near_far(1, 1000);
        PT(Camera) cam = new Camera("pssm-cam-" + to_string(i), lens);
        _cam_nodes.push_back(NodePath(cam));

    }
}

NodePath PSSMCameraRig::get_camera(int index) {
    nassertr(index >= 0 && index < _cam_nodes.size(), NodePath());
    return _cam_nodes[index];
}

void PSSMCameraRig::reparent_to(NodePath &parent) {
    nassertv(_cam_nodes.size() > 0);
    for (size_t i = 0; i < _cam_nodes.size(); ++i) {
        _cam_nodes[i].reparent_to(parent);
    }
    _parent = parent;
}


LMatrix4f PSSMCameraRig::compute_mvp(int cam_index) {
    Camera* cam = DCAST(Camera, _cam_nodes[cam_index].node());
    LMatrix4f transform = _parent.get_transform(_cam_nodes[cam_index])->get_mat();
    return transform * cam->get_lens()->get_view_mat() * cam->get_lens()->get_projection_mat();
}


float get_split_start(size_t split_index, size_t max_splits) {
    // Use a pure logarithmic split scheme for now
    float linear_factor = (float)split_index / (float)max_splits;

    // Split is computed as: k = log(linear + 1.0);
    // Assuming we have k, then we need exp(k) - 1.0

    return exp(linear_factor) - 1.0;
}


LPoint3f PSSMCameraRig::get_interpolated_point(CoordinateOrigin origin, float depth) {
    nassertr(depth >= 0.0 && depth <= 1.0, NULL);  
    return _curr_near_points[origin] * (1.0 - depth) + _curr_far_points[origin] * depth;   
}

const PTA_LMatrix4f &PSSMCameraRig::get_mvp_array() {
    return _camera_mvps;
}


LPoint3f PSSMCameraRig::get_snap_offset(LMatrix4f mat, int resolution) {

    // LPoint4f base_point = mat.get_row(3);
    LPoint4f base_point = mat.xform(LPoint4f(0, 0, 0, 1));
    base_point *= 0.5; base_point += 0.5;

    float texel_size = 1.0 / (float)(resolution);

    float offset_x =  fmod(base_point.get_x(), texel_size);
    float offset_y =  fmod(base_point.get_y(), texel_size);

    // Reproject the offset back, for that we need the inverse MVP
    mat.invert_in_place();
    LPoint4f new_base_point = mat.xform(LPoint4f(
            (base_point.get_x() - offset_x) * 2.0 - 1.0,
            (base_point.get_y() - offset_y) * 2.0 - 1.0,
            base_point.get_z() * 2.0 - 1.0, 1));

    return LPoint3f(
        -new_base_point.get_x(),
        -new_base_point.get_y(),
        -new_base_point.get_z());
}


LPoint3f get_average_of_points(LVecBase3f const (&starts)[4], LVecBase3f const ( &ends)[4]) {
    LPoint3f mid_point(0, 0, 0);

    // Sum all points and get the average
    for (size_t k = 0; k < 4; ++k) {
        mid_point += starts[k];
        mid_point += ends[k];
    }

    return mid_point / 8.0;
}


void find_min_max_extents(LVecBase3f &min_extent, LVecBase3f &max_extent, const LMatrix4f &transform, LVecBase3f const (&proj_points)[8], Camera *cam) {

    min_extent.set(1e10, 1e10, 1e10);
    max_extent.set(-1e10, -1e10, -1e10);
    LPoint2f screen_points[8];

    // Now project all points to the screen space of the current camera and also
    // find the minimum and maximum extents
    for (size_t k = 0; k < 8; ++k) {
        LVecBase4f point(proj_points[k], 1);
        LPoint4f proj_point = transform.xform(point);
        LPoint3f proj_point_3d(proj_point.get_x(), proj_point.get_y(), proj_point.get_z());
        cam->get_lens()->project(proj_point_3d, screen_points[k]);

        // Find min / max extents
        if (screen_points[k].get_x() > max_extent.get_x()) max_extent.set_x(screen_points[k].get_x());
        if (screen_points[k].get_y() > max_extent.get_y()) max_extent.set_y(screen_points[k].get_y());
        
        if (screen_points[k].get_x() < min_extent.get_x()) min_extent.set_x(screen_points[k].get_x());
        if (screen_points[k].get_y() < min_extent.get_y()) min_extent.set_y(screen_points[k].get_y());

        // Find min / max projected depth to adjust far plane
        if (proj_point.get_y() > max_extent.get_z()) max_extent.set_z(proj_point.get_y());
        if (proj_point.get_y() < min_extent.get_z()) min_extent.set_z(proj_point.get_y());
    }
}

void get_film_properties(LVecBase2f &film_size, LVecBase2f &film_offset, const LVecBase3f &min_extent, const LVecBase3f &max_extent) {
    float x_center = (min_extent.get_x() + max_extent.get_x()) * 0.5;
    float y_center = (min_extent.get_y() + max_extent.get_y()) * 0.5;
    float x_size = max_extent.get_x() - x_center;
    float y_size = max_extent.get_y() - y_center;
    film_size.set(x_size, y_size);
    film_offset.set(x_center * 0.5, y_center * 0.5);
}

void merge_points_interleaved(LVecBase3f (&dest)[8], LVecBase3f const (&array1)[4], LVecBase3f const (&array2)[4]) {
    for (size_t k = 0; k < 4; ++k) {
        dest[k] = array1[k];
        dest[k+4] = array2[k];
    }
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

        // Compute approximate split mid point: 
        LPoint3f split_mid = get_average_of_points(start_points, end_points);
        LPoint3f cam_start = split_mid + light_vector * _sun_distance; 

        // Reset the film size, offset and far-plane
        Camera* cam = DCAST(Camera, _cam_nodes[i].node());
        cam->get_lens()->set_film_size(1, 1);
        cam->get_lens()->set_film_offset(0, 0);
        cam->get_lens()->set_near_far(1, 100);

        // Find a good initial position
        _cam_nodes[i].set_pos(cam_start);
        _cam_nodes[i].look_at(split_mid);

        if (!_use_fixed_film_size) {

            // Collect all points which define the frustum
            LVecBase3f proj_points[8];
            merge_points_interleaved(proj_points, start_points, end_points);


            // Try out all angles
            float best_angle = 0.0;
            float best_angle_score = 1000000.0;
            LVecBase3f best_min_extent, best_max_extent;

            for (int angle = 0; angle < 360; ++angle) {

                // Set transform
    
                // Find minimum and maximum extends of the points
                LVecBase3f min_extent, max_extent;
                LMatrix4f merged_transform = _parent.get_transform(_cam_nodes[i])->get_mat();
                find_min_max_extents(min_extent, max_extent, merged_transform, proj_points, cam);

                LVecBase2f film_size, film_offset;
                get_film_properties(film_size, film_offset, min_extent, max_extent);

                float score = film_size.get_x() * film_size.get_x() + film_size.get_y() * film_size.get_y();

                if (score < best_angle_score) {
                    best_angle = angle;
                    best_angle_score = score;
                    best_min_extent = min_extent;
                    best_max_extent = max_extent;
                }
            }

            cout << "Best angle was at" << best_angle << endl;

            LVecBase2f film_size, film_offset;
            get_film_properties(film_size, film_offset, best_min_extent, best_max_extent);


            // Compute new film size
            cam->get_lens()->set_film_size(film_size);

            // Compute new film offset
            cam->get_lens()->set_film_offset(film_offset);

            // cam->get_lens()->set_near_far(50, max_extent.get_z());
            cam->get_lens()->set_near_far(best_min_extent.get_z(), best_max_extent.get_z());

        } else {

            cam->get_lens()->set_film_size(30, 30);
            cam->get_lens()->set_near_far(400, 600.0);
        }

        // Compute the camera MVP
        LMatrix4f mvp = compute_mvp(i);

        // Stable CSM Snapping
        if (false) {
            LPoint3f snap_offset = get_snap_offset(mvp, _resolution);
            _cam_nodes[i].set_pos(_cam_nodes[i].get_pos() + snap_offset);

            // Compute the new mvp, since we changed the snap offset
            mvp = compute_mvp(i);
        }

        _camera_mvps.set_element(i, mvp);
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

