
#include "PSSMCameraRig.h"

#include "orthographicLens.h"


PSSMCameraRig::PSSMCameraRig(int num_cameras) {
    init_cameras(num_cameras);
}

PSSMCameraRig::~PSSMCameraRig() {

}


void PSSMCameraRig::init_cameras(int num_cameras) {

    for (int i = 0; i < num_cameras; ++i)
    {
        Lens *lens = new OrthographicLens();
        lens->set_film_size(1, 1);
        lens->set_near_far(1, 1000);
        PT(Camera) cam = new Camera("pssm-cam-" + i, lens);
    }

}




void PSSMCameraRig::fit_to_camera(NodePath &cam_node, const LVecBase3f &light_vector) {

    const LMatrix4f &transform = cam_node.get_transform()->get_mat();

    Camera *cam = DCAST(Camera, cam_node.node());
    nassertv(cam != NULL);

    // Extract near and far points
    // Order: UL, UR, LL, LR
    // (Upper Left, Upper Right, Lower Left, Lower Right)
    LVecBase3f near_points[4];
    LVecBase3f far_points[4];



}

