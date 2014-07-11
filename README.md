Deferred Render Pipeline
==============

Complete deferred render pipeline for panda3d (Work in progress).
Wiki & Instructions how to setup: https://github.com/tobspr/RenderPipeline/wiki




#### Planned Features:

##### Deferred rendering (obviously)
- Still allows some objects to have forward passes

##### Early-Z
- Pre-Renders depth to avoid overdraw

##### SSDO
- with one bounce for indirect lighting / color bleeding

##### PSSM, Cloud Shadows, Large Terrain Shadows
- ~~complete lighting and shadows via compute shader~~
    - Too slow, replaced by regular fragment shaders

##### Atmospheric Scattering & Volumetric Fog

##### Multi-Hemisphere-Skybox

##### Lighting:
- Point Lights
    - Either shadow casting or not
    - When shadow casting, only use 2 perspectives
        - Parabolic mapping

- Directional Lights
    - Sun only
    - PSSM Shadows

- Ambient Lights
    - Darken or Bright
        - Artist controlled Global Illumination

- Projector Lights
    - Either shadow casting or not
    - Only 1 perspective
    - Projection texture
        - Can be used for flashlights for example

- Area Lights
    - Caster is a rectangle
        - Orthographic Lens
    - Also supports projection texture
    - Maybe Cone-Mapping

##### Physically based shading / lighting

##### Precomputed HDR environment probes
- Only in areas where reflective materials are used
    - and SSLR does not work well for the material
        - like water patches
- Image based lighting

##### Dynamic reflections
- Screen Space Local Reflections
- For specular materials
- Cheapest solution for reflections

##### Dynamic cubemaps 
- rare usage, because of performance
- Render only 2 perspectives, parabolic mapping
- Not updated every frame

##### Tone mapping (HDR)

##### Blur
- Focal Blur
- Movement Blur (edges)
- Mipmap based + in place 4x4 kernel
    - Varying radius (DOF)

##### Tesselation Shader
- Based on displacement map, or detail normals
- Height stored in z component of normalmap

##### Bokeh DOF
- In combination with blur

##### Approximated Chromatic Aberration


Thanks especially to rdb and all the others for support & help!
