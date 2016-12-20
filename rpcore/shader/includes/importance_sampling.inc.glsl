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

// From:
// http://www.trentreed.net/blog/physically-based-shading-and-image-based-lighting/
vec2 hammersley(uint i, uint N)
{
    return vec2(float(i) / float(N), float(bitfieldReverse(i)) * 2.3283064365386963e-10);
}




// From:
// http://www.gamedev.net/topic/655431-ibl-problem-with-consistency-using-ggx-anisotropy/

// http://blog.tobias-franke.eu/2014/03/30/notes_on_importance_sampling.html
vec3 importance_sample_ggx(vec2 xi, float alpha)
{
    float phi = TWO_PI * xi.x;
    float cos_theta_sq = (1.0 - xi.y) / max(1e-10, (alpha * alpha - 1.0) * xi.y + 1.0);
    cos_theta_sq = max(0, cos_theta_sq);

    float cos_theta = sqrt(cos_theta_sq);
    float sin_theta = sqrt(1.0 - cos_theta_sq);

    return vec3(sin_theta * cos(phi), sin_theta * sin(phi), cos_theta);
}



vec4 importance_sample_ggx_pdf(vec2 E, float alpha)
{
	float m = alpha;
	float m2 = m * m;
	float phi = 2 * M_PI * E.x;
	float cos_theta = sqrt((1 - E.y) / (1 + (m2 - 1) * E.y));
	float sin_theta = sqrt(1 - cos_theta * cos_theta);

	vec3 h;
	h.x = sin_theta * cos(phi);
	h.y = sin_theta * sin(phi);
	h.z = cos_theta;

	float d = (cos_theta * m2 - cos_theta) * cos_theta + 1;
	float D = m2 / (M_PI * d * d);
	float pdf = D * cos_theta;

	return vec4(h, pdf);
}

vec3 importance_sample_lambert(vec2 Xi)
{
    float phi = TWO_PI * Xi.x;
    float cos_theta_sq = Xi.y;
    float cos_theta = sqrt(cos_theta_sq);
    float sin_theta = sqrt(1 - Xi.y);
    return vec3(sin_theta * cos(phi), sin_theta * sin(phi), cos_theta);
}


vec3 sample_hemisphere(vec2 Xi)
{
    float phi = TWO_PI * Xi.x;
    float cos_theta_sq = Xi.y;
    float cos_theta = sqrt(cos_theta_sq);
    float sin_theta = sqrt(1 - Xi.y);
    return vec3(sin_theta * cos(phi), sin_theta * sin(phi), cos_theta);
}

vec3 tangent_to_world(vec3 t, vec3 n)
{
    vec3 tangent, binormal;
    find_arbitrary_tangent(n, tangent, binormal);
    return normalize(t.z * n + t.y * tangent + t.x * binormal);
}
