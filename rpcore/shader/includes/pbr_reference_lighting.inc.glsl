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

#pragma include "includes/material.inc.glsl"
#pragma include "includes/brdf.inc.glsl"
#pragma include "includes/noise.inc.glsl"
#pragma include "includes/importance_sampling.inc.glsl"

// Prevent unnecessary shader compiler work
#if SPECIAL_MODE_ACTIVE(GROUND_TRUTH)

float fr_cos_theta(vec3 v) { return v.z; }
float fr_cos_theta_2(vec3 v) { return v.z * v.z; }
float fr_sin_theta_2(vec3 v) { return 1.0 - v.z * v.z; }
float fr_sin_theta(vec3 v) { return sqrt(max(0.0, fr_sin_theta_2(v))); }
float fr_tan_theta(vec3 v) { float temp = max(0, 1.0 - v.z * v.z); return sqrt(temp) / v.z; }
float fr_tan_theta_2(vec3 v) { float temp = max(0, 1.0 - v.z * v.z); return temp / (v.z * v.z); }
float fr_sin_phi(vec3 v) { return v.y / fr_sin_theta(v); }
float fr_cos_phi(vec3 v) { return v.x / fr_cos_theta(v); }

float hypot2(float a, float b) {
	float r;
	if (abs(a) > abs(b)) {
		r = b / a;
		r = abs(a) * sqrt(1.0 + r * r);
	} else if (b != 0.0) {
		r = a / b;
		r = abs(b) * sqrt(1.0 + r * r);
	} else {
		r = 0.0f;
	}
	return r;
}


struct RefRay {
    vec3 l;
    vec3 o;
};

struct RefSphere {
    vec3 c;
    float r;
};

float ggx_ndf(Material m, vec3 h) {
    float alpha_sq = m.roughness * m.roughness;
    float cos_theta_2 = fr_cos_theta_2(h);
    float beckmann_exponent = ((h.x * h.x) + (h.y * h.y)) / (alpha_sq * cos_theta_2);
    float root = (1.0 + beckmann_exponent) * cos_theta_2;
    float result = 1.0 / (M_PI * alpha_sq * root * root);
    if (result * fr_cos_theta(h) < 1e-20)
        return 0.0;
    return result;
}

float ggx_pdf(Material m, vec3 h) {
    return ggx_ndf(m, h) * fr_cos_theta(h);
}

vec3 ggx_importance_sample(Material m, vec2 xi, out float pdf) {
    float sin_phi_m = sin(xi.y * TWO_PI);
    float cos_phi_m = cos(xi.y * TWO_PI);
    float alpha_sqr = m.roughness * m.roughness;
    float tan_theta_m_sqr = alpha_sqr * xi.x / (1.0 - xi.x);
    float cos_theta_m = 1.0 / sqrt(1.0 + tan_theta_m_sqr);
    float temp = 1.0 + tan_theta_m_sqr / alpha_sqr;
    pdf = ONE_BY_PI / (alpha_sqr * cos_theta_m * cos_theta_m * cos_theta_m * temp * temp); 
    float sin_theta_m = sqrt(max(0, 1 - cos_theta_m * cos_theta_m));

    return vec3(
			sin_theta_m * cos_phi_m,
			sin_theta_m * sin_phi_m,
			cos_theta_m
		);
}


vec2 square_to_uniform_disk_concentric(vec2 xi) {
	float r1 = 2.0f*xi.x - 1.0f;
	float r2 = 2.0f*xi.y - 1.0f;

	/* Modified concencric map code with less branching (by Dave Cline), see
	   http://psgraphics.blogspot.ch/2011/01/improved-code-for-concentric-map.html */
	float phi, r;
	if (r1 == 0 && r2 == 0) {
		r = phi = 0;
	} else if (r1*r1 > r2*r2) {
		r = r1;
		phi = (M_PI/4.0f) * (r2/r1);
	} else {
		r = r2;
		phi = (M_PI/2.0f) - (r1/r2) * (M_PI/4.0f);
	}

    float cosPhi = cos(phi);
    float sinPhi = sin(phi);
	return vec2(r * cosPhi, r * sinPhi);
}


/// Density of \ref squareToCosineHemisphere() with respect to solid angles
float square_to_cosine_hemisphere_pdf(vec3 d)
{
    return ONE_BY_PI * fr_cos_theta(d);
}

vec3 square_to_cosine_hemisphere(vec2 xi) {
	vec2 p = square_to_uniform_disk_concentric(xi);
    float z = sqrt(max(0, 1.0f - p.x*p.x - p.y*p.y));

	/* Guard against numerical imprecisions */
	if (abs(z) < 1e-10)
		z = 1e-10;

	return vec3(p.x, p.y, z);
}


vec3 lambert_importance_sample(Material m, vec2 xi, out float pdf) {
    vec3 result = square_to_cosine_hemisphere(xi);
    pdf = square_to_cosine_hemisphere_pdf(result);
    return result;
}

vec3 fresnel(Material m, float LxH) {
    vec3 f0 = mix(vec3(m.specular), m.basecolor, m.metallic);
    vec3 f90 = vec3(1);
    return mix(f0, vec3(f90), pow(2, (-5.55473 * LxH - 6.98316) * LxH));
}


float smith_g1(Material m, vec3 v, vec3 h) {
    if (dot(v, h) * fr_cos_theta(v) <= 0)
        return 0.0f;

    float tan_theta = abs(fr_tan_theta(v));
    if (tan_theta == 0.0)
        return 1.0;

    float alpha = m.roughness;
    float root = alpha * tan_theta;
    return 2.0 / (1.0 + hypot2(1.0, root));
}

float brdf_G(Material m, vec3 wi, vec3 wo, vec3 h) {
    return smith_g1(m, wi, h) * smith_g1(m, wo, h);
}

bool ray_sphere_intersection(RefRay r, RefSphere s)
{
    vec3 oc = r.o - s.c;
    float below_root = square(dot(r.l, oc)) - length_squared(oc) + square(s.r);
    if (below_root < 0)
        return false;

    float pre = -dot(r.l, oc);
    float d1 = pre + sqrt(below_root);
    return d1 > 0;

    // return true;
 
    // return sq >= 0 && pre > -pre;
}

// Convert from Global to local coordinates
vec3 convert_system(vec3 v, mat3 system) {
    return vec3( // could use mul
        dot(v, system[0]),
        dot(v, system[1]),
        dot(v, system[2])
    );
}

vec3 convert_system(vec3 v, mat3 system, vec3 origin) {
    v -= origin;
    return vec3( // could use mul
        dot(v, system[0]),
        dot(v, system[1]),
        dot(v, system[2])
    );
}


vec3 process_spherelight_reference(Material m, LightData light, vec3 v, float shadow) {

    const uint num_samples = 64;
    vec3 accum = vec3(0);

    // Construct transformation from world to tangent space
    vec3 tangent, binormal;
    find_arbitrary_tangent(m.normal, tangent, binormal);
    mat3 system = mat3(
        tangent,
        binormal,
        m.normal
    );

    v = convert_system(v, system);
    vec3 r = -reflect(v, vec3(0, 0, 1));
    float jitter = rand(ivec2(gl_FragCoord.xy) * 0.23423 + 0.86342 * mod(MainSceneData.frame_index, 512));

    RefSphere sphere;
    sphere.c = convert_system(get_light_position(light), system, m.position);
    sphere.r = get_spherelight_sphere_radius(light);

    RefRay ray;
    ray.o = vec3(0);

    // Convert from luminance to luminous power
    vec3 light_emitting_color = get_light_color(light);
    light_emitting_color /= 4.0 * sphere.r * sphere.r * M_PI * M_PI;

    // Specular
    for (uint i = 0; i < num_samples; ++i) {
        vec2 xi = hammersley(i, num_samples);
        xi.x = mod(xi.x + 6.283926 * jitter, 1.0); 
        xi.y = mod(xi.y + 5.852342 * jitter, 1.0); 

        float pdf;
        vec3 h = ggx_importance_sample(m, xi.xy, pdf);
        vec3 l = 2.0 * dot(v, h) * h - v;
        ray.l = l;

        if (ray_sphere_intersection(ray, sphere)) {
            float ndf = ggx_ndf(m, h);
            vec3 fresnel = fresnel(m, saturate(dot(l, h)));
            float visibility = brdf_G(m, l, v, h);

            accum += ndf * fresnel * visibility / max(1e-3, 4.0 * fr_cos_theta(h) * pdf);

            // accum += fresnel * ndf * visibility * saturate(dot(l, h)) / (pdf * fr_cos_theta(l));
        }
    }

    accum /= num_samples;
    accum *= light_emitting_color;
    // accum *= 0;

    // Diffuse
    #if 1
    float eta = m.specular_ior / AIR_IOR;
    float inv_eta_2 = 1.0 / (eta * eta);
    inv_eta_2 = 1;

    // vec3 diff_color = m.basecolor * (1 - m.metallic) * inv_eta_2 * ONE_BY_PI;
    vec3 diff_color = m.basecolor * (1 - m.metallic) * inv_eta_2;
    vec3 diff_accum = vec3(0);

    for (uint i = 0; i < num_samples; ++i) {
        vec2 xi = hammersley(i, num_samples);
        xi.x = mod(xi.x + 3.582343 * jitter, 1.0); 
        xi.y = mod(xi.y + 5.852342 * jitter, 1.0); 

        float pdf;
        vec3 h = lambert_importance_sample(m, xi.yx, pdf);
        vec3 l = 2.0 * dot(v, h) * h - v;
        ray.l = l;

        if (ray_sphere_intersection(ray, sphere)) {
            // XXX: missing divide by pdf?!
            diff_accum += diff_color * ONE_BY_PI * fr_cos_theta(l);
        }
    }

    diff_accum /= num_samples;
    diff_accum *= light_emitting_color;
    accum += diff_accum;

    #else
        vec3 l = normalize(m.position - get_light_position(light));
        // accum = ONE_BY_PI * saturate(dot(m.normal, l));
        // accum = vec3(ONE_BY_PI);
        accum = m.basecolor * ONE_BY_PI * saturate(dot(m.normal, -l));
        // accum *= get_light_color(light);
        // accum *= light_emitting_color;
    #endif

    accum *= shadow;


    return vec3(accum);
}


#endif // GROUND_TRUTH
