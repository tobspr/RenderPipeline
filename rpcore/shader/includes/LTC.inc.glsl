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


 /*

Real-Time Polygonal-Light Shading with Linearly Transformed Cosines
Eric Heitz, Jonathan Dupuy, Stephen Hill and David Neubelt

ACM SIGGRAPH 2016

https://eheitzresearch.wordpress.com/415-2/

 */

#define LTC_MAX_VERTICES 16

uniform sampler2D LTCMatTex;
uniform sampler2D LTCAmpTex;


mat3 mat3_from_rows(vec3 c0, vec3 c1, vec3 c2)
{
    return transpose(mat3(c0, c1, c2));
}

vec2 LTC_Coords(float cosTheta, float roughness)
{
    float theta = acos(cosTheta);
    vec2 coords = vec2(roughness, theta/(0.5*3.14159));

    const float LUT_SIZE = 32.0;
    // scale and bias coordinates, for correct filtered lookup
    coords = coords * (LUT_SIZE - 1.0) / LUT_SIZE + 0.5 / LUT_SIZE;
    coords.y = 1 - coords.y;
    return coords;
}

mat3 LTC_Matrix(sampler2D texLSDMat, vec2 coord)
{
    // load inverse matrix
    vec4 t = textureLod(texLSDMat, coord, 0);
    mat3 Minv = mat3(
        vec3(1,     0, t.y),
        vec3(  0, t.z,   0),
        vec3(t.w,   0, t.x)
    );
    return Minv;
}

float LTC_IntegrateEdge(vec3 v1, vec3 v2)
{
    float cosTheta = dot(v1, v2);
    cosTheta = clamp(cosTheta, -0.9999, 0.9999);
    float theta = acos(cosTheta);
    float res = cross(v1, v2).z * theta / sin(theta);
    return res;
}

vec3 LTC_Evaluate(vec3 N, vec3 V, vec3 P, mat3 Minv, vec3 points[LTC_MAX_VERTICES], const int num_vertices)
{
    // construct orthonormal basis around N
    vec3 T1, T2;
    T1 = normalize(V - N*dot(V, N));
    T2 = cross(N, T1);

    // rotate area light in (T1, T2, R) basis
    Minv = Minv * mat3_from_rows(T1, T2, N);

    for (int i = 0; i < num_vertices; ++i) {
        points[i] = Minv * (points[i] - P);
        points[i].z = max(0.0, points[i].z); // fast clipping
        points[i] = normalize(points[i]);
    }

    // integrate
    float sum = LTC_IntegrateEdge(points[num_vertices - 1], points[0]);

    for (int i = 0; i < num_vertices - 1; ++i) {
        sum += LTC_IntegrateEdge(points[i], points[i + 1]);
    }

    sum = max(0.0, -sum);
    return vec3(sum);
}


// Helper for the compiler, it cannot properly unroll the loops even when
// the number of vertices is known (4). Not sure why, but this is much faster.
vec3 LTC_EvaluateRect(vec3 N, vec3 V, vec3 P, mat3 Minv, vec3 points[4])
{
    // construct orthonormal basis around N
    vec3 T1, T2;
    T1 = normalize(V - N*dot(V, N));
    T2 = cross(N, T1);

    // rotate area light in (T1, T2, R) basis
    Minv = Minv * mat3_from_rows(T1, T2, N);

    for (int i = 0; i < 4; ++i) {
        points[i] = Minv * (points[i] - P);
        points[i].z = max(0.0, points[i].z); // fast clipping
        points[i] = normalize(points[i]);
    }

    // integrate
    float sum = LTC_IntegrateEdge(points[3], points[0]);

    for (int i = 0; i < 3; ++i) {
        sum += LTC_IntegrateEdge(points[i], points[i + 1]);
    }

    sum = max(0.0, -sum);
    return vec3(sum);
}
