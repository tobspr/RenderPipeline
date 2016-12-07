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

#pragma once



// Creates a rotation mat, rotation should be 0 .. 2 * pi
mat2 make_rotate_mat2(float rotation) {
    float r_sin = sin(rotation);
    float r_cos = cos(rotation);
    return mat2(r_cos, -r_sin, r_sin, r_cos);
}

// Creates a identity mat
mat2 make_ident_mat2() {
    return mat2(
        1, 0,
        0, 1
    );
}

// Creates a scale matrix
mat2 make_scale_mat2(float scale) {
    return mat2(
        scale, 0,
        0, scale
    );
}

// Creates a identity mat
mat3 make_ident_mat3() {
    return mat3(
        1, 0, 0,
        0, 1, 0,
        0, 0, 1
    );
}

// Makes a matrix to rotate arround the X axis with the given angle (should be in radians)
mat3 make_rotate_mat3_x(float rot_radians) {
    float cos_x = cos(rot_radians), sin_x = sin(rot_radians);
    return mat3(
        1, 0, 0,
        0, cos_x, -sin_x,
        0, sin_x, cos_x
    );   
}


// Makes a matrix to rotate arround the Y axis with the given angle (should be in radians)
mat3 make_rotate_mat3_y(float rot_radians) {
    float cos_y = cos(rot_radians), sin_y = sin(rot_radians);
    return mat3(
        cos_y, 0, sin_y,
        0, 1, 0,
        -sin_y, 0, cos_y
    );
}

// Makes a matrix to rotate arround the Z axis with the given angle (should be in radians)
mat3 make_rotate_mat3_z(float rot_radians) {
    float cos_z = cos(rot_radians), sin_z = sin(rot_radians);
    return mat3(
        cos_z, -sin_z, 0,
        sin_z, cos_z, 0,
        0, 0, 1
    );
}

// Makes a matrix to rotate in the given rotations around the x, y and z axis (should be in radians)
mat3 make_rotate_mat3(float rotate_x, float rotate_y, float rotate_z) {
    return make_rotate_mat3_x(rotate_x) *
           make_rotate_mat3_y(rotate_y) *
           make_rotate_mat3_z(rotate_z);
}


// Creates a scale matrix
mat3 make_scale_mat3(float scale) {
    return mat3(
        scale, 0, 0,
        0, scale, 0,
        0, 0, scale
    );
}
