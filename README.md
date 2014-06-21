Render Pipeline
==============

Complete deferred render pipeline for panda3d

## Features:

### Deferred rendering
    - But still allows some objects to have forward passes

### Early Z
    - Pre-Renders depth to avoid overdraw

### SSDO
    -> + one bounce for indirect lighting / color bleeding
    

### PSSM, Cloud Shadows, Large Terrain Shadows
    -> complete lighting + shadows via compute shader

### Atmospheric Scattering + Volumetric Fog

### Multi-Hemisphere-Skybox

### Lighting:
    - Point Lights
        - Either shadow casting or not
        - When shadow casting, only use 2 perspectives
            -> Parabolic mapping

    - Directional Lights
        - Sun only

    - Ambient Lights
        - Darken or Bright
            -> Artist controlled AO

    - Projector Lights
        - Either shadow casting or not
        - Only 1 perspective
        - Projection texture
            -> Can be used for flashlights for example

    - Area Lights
        - Caster is a rectangle
            -> Orthographic Lens
        - Also supports projection texture
        - Cone-Mapping

### Physically based shading / lighting

### Precomputed HDR environment probes
    -> Only in areas where reflective materials are used
        -> and SSLR does not match
    -> Image based lighting

### Dynamic reflections (Screen Space local reflections)
    -> For specular materials

### Dynamic cubemaps (rare usage, because of performance)
    -> Render only 2 perspectives, parabolic mapping
    -> Not updated every frame

### Tone mapping (HDR)

### Blur
    -> Focal Blur
    -> Movement Blur (edges)
    -> Mipmap based + in place 4x4 kernel
        -> Adjustable radius

### Tesselation Shader
    -> Based on displacement map, or detail normals
    -> Height stored in z component of normalmap