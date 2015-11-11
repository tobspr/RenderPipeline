
#include "PSSMCameraRig.h"

#include <cmath>
#include "orthographicLens.h"


PSSMCameraRig::PSSMCameraRig(size_t num_splits) {
    nassertv(num_splits > 0 && num_splits <= MAX_PSSM_SPLITS);
    _pssm_distance = 100.0;
    _sun_distance = 500.0;
    _use_fixed_film_size = false;
    _find_tight_frustum = true;
    _use_stable_csm = true;
    _resolution = 512;
    _camera_mvps = PTA_LMatrix4f::empty_array(num_splits);
    _camera_rotations = PTA_float::empty_array(num_splits);
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

void PSSMCameraRig::set_use_fixed_film_size(bool flag) {
    _use_fixed_film_size = flag;
}

void PSSMCameraRig::set_use_tight_frustum(bool flag) {
    _find_tight_frustum = flag;
}

void PSSMCameraRig::set_resolution(int resolution) {
    _resolution = resolution;
}

void PSSMCameraRig::set_use_stable_csm(bool flag) {
    _use_stable_csm = flag;
}

void PSSMCameraRig::reset_film_size_cache() {
    for (size_t i = 0; i < _max_film_sizes.size(); ++i) {
        _max_film_sizes[i].set(0, 0);
    }
}



void PSSMCameraRig::init_cam_nodes(size_t num_splits) {
    _cam_nodes.reserve(num_splits);
    _max_film_sizes.resize(num_splits);
    for (size_t i = 0; i < num_splits; ++i)
    {
        Lens *lens = new OrthographicLens();
        lens->set_film_size(1, 1);
        lens->set_near_far(1, 1000);
        PT(Camera) cam = new Camera("pssm-cam-" + to_string(i), lens);
        _cam_nodes.push_back(NodePath(cam));
        _max_film_sizes[i].set(0, 0);
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

const PTA_float &PSSMCameraRig::get_rotation_array() {
    return _camera_rotations;
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


LVecBase3f get_angle_vector(float progress) {
    LVecBase3f result(0, 1.0 - progress, progress);
    // LVecBase3f result(1 - progress, 0, progress);
	result.normalize();
    return result;
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

        // Reset rotation
        _camera_rotations[i] = 0.0;


        // Collect all points which define the frustum
        LVecBase3f proj_points[8];
        merge_points_interleaved(proj_points, start_points, end_points);
        LVecBase3f best_min_extent, best_max_extent;

        // Disable angle-finding in case we don't use a tight frustun
        if (_find_tight_frustum) {

            // Try out all angles
            const int num_iterations = 90;
            float best_angle = 0.0;
            float best_angle_score = 1e20;
            float normal_angle_score = 0;

            for (float progress = 0.0; progress < 1.0; progress += 1.0 / (float)num_iterations) {

                // Apply the angle to the camera rotation
                _cam_nodes[i].look_at(split_mid, get_angle_vector(progress));

                // Find minimum and maximum extents of the points
                LVecBase3f min_extent, max_extent;
                LMatrix4f merged_transform = _parent.get_transform(_cam_nodes[i])->get_mat();
                find_min_max_extents(min_extent, max_extent, merged_transform, proj_points, cam);

                // Get the minimum film size required to cover all points
                LVecBase2f film_size, film_offset;
                get_film_properties(film_size, film_offset, min_extent, max_extent);

                // The "score" is the area of the film, smaller values are better,
                // since we render less objects then
                float score = film_size.get_x() * film_size.get_y();

                // cout << "\tAngle " << progress << " has a score of " << score << " with a vec of " << get_angle_vector(progress) << endl;

                if (score < best_angle_score) {
                    best_angle = progress;
                    best_angle_score = score;
                    best_min_extent = min_extent;
                    best_max_extent = max_extent;
                }

                if (progress == 0.0) {
                    normal_angle_score = score;
                }
            }
            _cam_nodes[i].look_at(split_mid, get_angle_vector(best_angle));
            _camera_rotations[i] = best_angle;
        } else {
            // Find minimum and maximum extents of the points
            LMatrix4f merged_transform = _parent.get_transform(_cam_nodes[i])->get_mat();
            find_min_max_extents(best_min_extent, best_max_extent, merged_transform, proj_points, cam);
        }

        LVecBase2f film_size, film_offset;
        get_film_properties(film_size, film_offset, best_min_extent, best_max_extent);

        if (_use_fixed_film_size) {
            // In case we use a fixed film size, store the maximum film size, and
            // only change the film size if a new maximum is there
            if (_max_film_sizes[i].get_x() < film_size.get_x()) _max_film_sizes[i].set_x(film_size.get_x());
            if (_max_film_sizes[i].get_y() < film_size.get_y()) _max_film_sizes[i].set_y(film_size.get_y());

            cam->get_lens()->set_film_size(_max_film_sizes[i]);

        } else {
            
            // Set actual film size
            cam->get_lens()->set_film_size(film_size);
        }

        // Compute new film offset
        cam->get_lens()->set_film_offset(film_offset);

        cam->get_lens()->set_near_far(10, best_max_extent.get_z());


        // Compute the camera MVP
        LMatrix4f mvp = compute_mvp(i);

        // Stable CSM Snapping
        if (_use_stable_csm) {
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

    // Check if a configuration error occured
    if (_use_fixed_film_size && _find_tight_frustum) {
        // If we use a fixed film size, we cannot use a tight frustum
        cout << "Warning: If you use a fixed film size, you cannot use the tight frustum option" << endl;
    }

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

