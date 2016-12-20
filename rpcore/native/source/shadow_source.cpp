/**
 *
 * RenderPipeline
 *
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

#include "shadow_source.h"

/**
 * @brief Constructs a new shadow source
 * @details This constructs a new shadow source, with no projection setup,
 *   and no slot assigned.
 */
ShadowSource::ShadowSource() {
    _slot = -1;
    _needs_update = true;
    _resolution = 512;
    _mvp.fill(0.0);
    _region.fill(-1);
    _region_uv.fill(0);
}

/**
 * @brief Setups a perspective lens for the source.
 * @details This makes the shadow source behave like a perspective lens. The
 *   parameters are similar to the ones of a PerspectiveLens.
 *
 * @param fov FoV of the lens
 * @param near_plane The near plane of the lens, to avoid artifacts at low distance
 * @param far_plane The far plane of the lens
 * @param pos Position of the lens, in world space
 * @param direction Direction (Orientation) of the lens
 */
void ShadowSource::set_perspective_lens(float fov, float near_plane,
      float far_plane, const LVecBase3f& pos, const LVecBase3f& direction, const LVecBase3f& up) {
    // Construct a temporary lens to generate the lens matrix
    PerspectiveLens temp_lens(fov, fov);
    temp_lens.set_film_offset(0, 0);
    temp_lens.set_near_far(near_plane, far_plane);
    temp_lens.set_view_vector(direction.normalized(), up.normalized());
    set_lens(temp_lens, pos);
}

/**
 * @brief Setups a generic lens for the source.
 * @details Setups the shadow source to use the given lens, at the given position.
 *
 * @param lens Lens to copy matrix from
 * @param pos Source/Lens position
*/

void ShadowSource::set_lens(const Lens& lens, LVecBase3f pos) {
    
    // Construct the transformation matrix
    set_matrix_lens(LMatrix4f::translate_mat(-pos) * lens.get_projection_mat());

    // Set new bounds, approximate with sphere
    CPT(BoundingHexahedron) hexahedron = DCAST(BoundingHexahedron, lens.make_bounds());
    LPoint3 center = (hexahedron->get_min() + hexahedron->get_max()) * 0.5f;
    _bounds = BoundingSphere(pos + center, (hexahedron->get_max() - center).length());

}
    