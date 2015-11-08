#pragma once

#pragma include "Includes/Configuration.inc.glsl"

// From:
// http://blog.tobias-franke.eu/2014/03/30/notes_on_importance_sampling.html
// vec2 importance_sample_phong(vec2 xi)
// {
//   float phi = 2.0f * M_PI * xi.x;
//   float theta = acos(pow(1.0f - xi.y, 1.0f/(n+1.0f)));
//   return vec2(phi, theta);
// }

// From:
// http://blog.tobias-franke.eu/2014/03/30/notes_on_importance_sampling.html
vec2 importance_sample_ggx(vec2 xi, float roughness)
{
  float phi = 2.0f * M_PI * xi.x;
  float theta = acos(sqrt((1.0f - xi.y)/
                          (( (roughness*roughness) - 1.0f) * xi.y + 1.0f)
                         ));
  return vec2(phi, theta);
}


// FROM:
// http://www.trentreed.net/blog/physically-based-shading-and-image-based-lighting/
// I like this method more, since it uses bitfieldReverse instead of a lot of shifts
vec2 Hammersley(uint i, uint N)
{
  return vec2(
    float(i) / float(N),
    float(bitfieldReverse(i)) * 2.3283064365386963e-10
  );
}


// FROM:
// http://www.gamedev.net/topic/655431-ibl-problem-with-consistency-using-ggx-anisotropy/
vec3 ImportanceSampleGGX(vec2 Xi, float roughness, vec3 n)
{
  float r_square = roughness * roughness;

  float phi = 2 * M_PI * Xi.x;
  float cos_theta = sqrt((1 - Xi.y) / (1 + (r_square*r_square - 1) * Xi.y));   
  float sin_theta = sqrt(1 - cos_theta * cos_theta);


  vec3 h;
  h.x = sin_theta * cos(phi);
  h.y = sin_theta * sin(phi);
  h.z = cos_theta;

  vec3 up_vector = abs(n.z) < 0.999 ? vec3(0, 0, 1) : vec3(1, 0, 0);
  vec3 tangent = normalize(cross(up_vector, n));
  vec3 bitangent = normalize(cross(n, tangent));

  // Tangent to world space
  return normalize(tangent * h.x + bitangent * h.y + n * h.z);
}

