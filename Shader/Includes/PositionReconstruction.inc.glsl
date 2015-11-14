#pragma once

uniform mat4 trans_clip_of_mainCam_to_mainRender;
uniform mat4 currentProjMatInv;
uniform mat4 currentProjMat;

// Constant values based on camera near and far plane
const float ndcNear = CAMERA_NEAR;
const float ndcFar = CAMERA_FAR;
const float ndcA = ndcNear + ndcFar;
const float ndcB = ndcNear - ndcFar;
const float ndcC = 2.0 * ndcNear * ndcFar;
const float ndcD = ndcFar - ndcNear;

float getZFromNdc(vec3 ndcPos) {
  return ndcC / (ndcA+(ndcPos.z * ndcB));
}

float getZFromNdc(vec3 ndcPos, float near, float far) {
  float d = ndcPos.z * (near-far);
  return ( (2.0 * near * far) / ((near + far) + d));
}

float getZFromLinearZ(float z) {
  z /= ndcC;
  z = 1.0 / z;
  z -= ndcA;
  z /= ndcB;
  z /= 2.0;
  z += 0.5;
  return z;
}

float getLinearZFromZ(float z) {
    return ndcC / (ndcA - (z * 2.0 - 1.0) * ndcD);
}

float getCustomLinearZFromZ(float z, float near, float far) {
    float z_n = z * 2.0 - 1.0;
    float z_e = 2.0 * near * far / (far + near - z_n * (far - near));
    return z_e;
}

float normalizeZ(float z, float near, float far) {
  return getCustomLinearZFromZ(z, near, far) / far;
}

vec3 calculateSurfacePos(float z, vec2 tcoord, mat4 clipToRender) {
  vec3 ndcPos = vec3(tcoord.xy, z) * 2.0 - 1.0;    
  vec4 clipPos = vec4(getZFromNdc(ndcPos));
  clipPos.xyz = ndcPos * clipPos.w;
  return (clipToRender * clipPos).xyz;
}

vec3 calculateSurfacePos(float z, vec2 tcoord) {
  return calculateSurfacePos(z, tcoord, trans_clip_of_mainCam_to_mainRender);
}

vec3 calculateSurfacePos(float z, vec2 tcoord, float near, float far, mat4 clipToRender) {
  vec3 ndcPos = vec3(tcoord.xy, z) * 2.0 - 1.0;    
  vec4 clipPos = vec4(getZFromNdc(ndcPos, near, far));
  clipPos.xyz = ndcPos * clipPos.w;
  return (clipToRender * clipPos).xyz;
}


vec3 calculateViewPos(float z, vec2 tcoord) {
  // vec3 ndc = vec3(tcoord, z) * 2.0 - 1.0;

  //@TODO: Use fma
  vec3 ndc = vec3(tcoord.xy * 2.0 - 1.0, z);
  vec4 sampleViewPos = inverse(currentProjMat) * vec4(ndc, 1.0);
  return sampleViewPos.xyz / sampleViewPos.w;
}

vec3 viewToScreen(vec3 view_pos) {
  vec4 projected = currentProjMat * vec4(view_pos, 1);
  projected.xyz /= projected.w;
  projected.xy = fma(projected.xy, vec2(0.5), vec2(0.5));
  return projected.xyz;
}