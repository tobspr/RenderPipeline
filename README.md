## Deferred Render Pipeline

This is my deferred render pipeline, implemented in Panda3D. This 
pipeline aims to do everything related to graphics for you, so that
the user can focus on making the game, and not the graphics.

This pipeline is still in developement, feel free to join :)
Thanks especially to rdb and all the others for support & help!


### Setup
You can find the wiki & instructions how to setup the pipeline at
https://github.com/tobspr/RenderPipeline/wiki

### Features

#### Deferred rendering
- Allows forward shading, too

#### Early-Z
- Pre-Renders depth to avoid overdraw
- Not sure if it's needed at all

#### Occlusion
- SSDO, SAO and HBAO

#### PSSM, Cloud Shadows, Large Terrain Shadows

#### Multi-Hemisphere-Skybox

#### Lighting:
- Point Lights
- Directional Lights
    - PSSM Shadows
- Sun Lights
    - Atmospheric Scattering
- Ambient Lights
    - Darken or Bright
        - Artist controlled Global Illumination
- Projector Lights
    - Either shadow casting or not
    - Projection texture
        - Can be used for flashlights for example
- Area Lights
    - Caster is a rectangle
    - Also supports projection texture
    - Maybe Cone-Mapping for penumbras?

#### Physically based shading / lighting

#### Precomputed HDR environment probes
- Only in areas where reflective materials are used
    - and SSLR does not work well for the material
        - like water patches
- Image based lighting

#### Dynamic reflections
- Screen Space Local Reflections for reflective materials
- Cheapest solution for reflections

#### Dynamic cubemaps 
- Rare usage, because of performance
- Not updated every frame

#### Tone mapping (HDR)

#### Blur
- Focal Blur
- Movement Blur (edges)
- Mipmap based + in place 4x4 kernel
    - Varying radius (DOF)
- Maybe Bokeh

#### Tesselation Shader displacement

#### Approximated Chromatic Aberration


