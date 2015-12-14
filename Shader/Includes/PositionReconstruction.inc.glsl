#pragma once

uniform mat4 trans_clip_of_mainCam_to_mainRender;
uniform mat4 trans_mainRender_to_view_of_mainCam;
uniform mat4 trans_mainRender_to_clip_of_mainCam;

uniform mat4 currentProjMatInv;
uniform mat4 currentProjMat;

// Constant values based on main camera near and far plane
const float ndcNear = CAMERA_NEAR;
const float ndcFar = CAMERA_FAR;
const float ndcA = ndcNear + ndcFar;
const float ndcB = ndcNear - ndcFar;
const float ndcC = 2.0 * ndcNear * ndcFar;
const float ndcD = ndcFar - ndcNear;

// Computes the Z component from a position in NDC space
float getZFromNdc(vec3 ndcPos) {
  return ndcC / (ndcA+(ndcPos.z * ndcB));
}


// Computes the Z component from a position in NDC space, with a given near and far plane
float getZFromNdc(vec3 ndcPos, float near, float far) {
  float d = ndcPos.z * (near-far);
  return ( (2.0 * near * far) / ((near + far) + d));
}

// Computes the Z component from linear Z
float getZFromLinearZ(float z) {
  // TODO: simplify
  z /= ndcC;
  z = 1.0 / z;
  z -= ndcA;
  z /= ndcB;
  z /= 2.0;
  z += 0.5;
  return z;
}

// Computes linear Z from a given Z value
float getLinearZFromZ(float z) {
    return ndcC / (ndcA - fma(z, 2.0, -1.0) * ndcD);
}

// Computes linear Z from a given Z value, and near and far plane
float getCustomLinearZFromZ(float z, float near, float far) {
    return 2.0 * near * far / (far + near - fma(z, 2.0, -1.0) * (far - near));
}

// Computes linear Z from a given Z value, and near and far plane, for orthographic projections
float getCustomLinearZFromOrthoZ(float z, float near, float far) {
  return 2.0 / (far + near - fma(z, 2.0, -1.0) * (far - near));
}

// Converts a nonlinear Z to a linear Z from 0 .. 1
float normalizeZ(float z, float near, float far) {
  return getCustomLinearZFromZ(z, near, far) / far;
}

// Computes the surface position based on a given Z, a texcoord, and the Inverse MVP matrix
vec3 calculateSurfacePos(float z, vec2 tcoord, mat4 clipToRender) {
  vec3 ndcPos = fma(vec3(tcoord.xy, z), vec3(2.0), vec3(-1.0));    
  vec4 clipPos = vec4(getZFromNdc(ndcPos));
  clipPos.xyz = ndcPos * clipPos.w;
  return (clipToRender * clipPos).xyz;
}

// Computes the surface position based on a given Z and a texcoord
vec3 calculateSurfacePos(float z, vec2 tcoord) {
  return calculateSurfacePos(z, tcoord, trans_clip_of_mainCam_to_mainRender);
}


// Computes the surface position based on a given Z and a texcoord, aswell as a
// custom near and far plane, and the inverse MVP. This is for orthographic projections
vec3 calculateSurfacePosOrtho(float z, vec2 tcoord, float near, float far, mat4 clipToRender) {
  vec3 ndcPos = fma(vec3(tcoord.xy, z), vec3(2.0), vec3(-1.0));
  vec4 clipPos = vec4(getCustomLinearZFromOrthoZ(ndcPos.z*0.5+0.5, near, far));
  clipPos.xyz = ndcPos * clipPos.w;
  vec4 result = clipToRender * clipPos;
  return result.xyz / result.w;
}

// Computes the view position from a given Z value and texcoord
vec3 calculateViewPos(float z, vec2 tcoord) {
  vec3 ndc = vec3( fma(tcoord.xy, vec2(2.0), vec2(-1.0)), z);
  vec4 sampleViewPos = inverse(currentProjMat) * vec4(ndc, 1.0);
  return sampleViewPos.xyz / sampleViewPos.w;
}

// Computes the NDC position from a given view position
vec3 viewToScreen(vec3 view_pos) {
  vec4 projected = currentProjMat * vec4(view_pos, 1);
  projected.xyz /= projected.w;
  projected.xy = fma(projected.xy, vec2(0.5), vec2(0.5));
  return projected.xyz;
}

// Converts a view space normal to world space
vec3 viewNormalToWorld(vec3 view_normal) {

  // Need to transform coordinate system, should't be required,
  // seems to be some bug

  view_normal = view_normal.xzy * vec3(1, -1, 1);
  return normalize((vec4(view_normal.xyz, 0) * trans_mainRender_to_view_of_mainCam).xyz);
}

// Converts a world space position to screen space position (NDC)
vec3 worldToScreen(vec3 world_pos) {
  vec4 proj = trans_mainRender_to_clip_of_mainCam * vec4(world_pos, 1);
  proj.xyz /= proj.w;
  proj.xy = fma(proj.xy, vec2(0.5), vec2(0.5));
  return proj.xyz;
}
