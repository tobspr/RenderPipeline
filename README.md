## Deferred Render Pipeline

This is my deferred render pipeline, implemented in Panda3D. This 
pipeline aims to handle the complete graphics pipeline, giving the user the ability to focus on making the game, and not the graphics.

Screenshot Thread: http://www.panda3d.org/forums/viewtopic.php?f=6&t=17050

### Screenshots

You can find more <a href="https://www.dropbox.com/sh/dq4wu3g9jwjqnht/AAABSOPnglDHZYsG5HXR-mhWa?dl=0">here</a>:

![Sponza](http://s7.directupload.net/images/140919/a6b3vyb5.png)
![Material Testing](http://s14.directupload.net/images/140919/ovfuulrt.png)
![Snow Material Test](http://s14.directupload.net/images/140919/aqzxkj3m.png)

This pipeline is still in developement, feel free to join :)
For questions & suggestions you can find me at #panda3d on freenode.

Thanks especially to rdb and all the others for support & help!

### Setup
You can find the wiki & instructions how to setup the pipeline at
https://github.com/tobspr/RenderPipeline/wiki

### Features

##### Deferred rendering
- Separate transparency and forward pass, too 

##### Occlusion
- SSDO, SAO and HBAO for high frequency AO
- Also voxel traced AO and GI for medium/low frequency AO

##### Global Illumination
- Cone traced Global Illumination
- Also cone traced Specular Reflections
    - Better results than screen space reflections
    - Blurred reflections are cheap

##### Dynamic Scene Voxelization
- Used for multiple effects like GI, or specular reflections
- Allows correct specular refletions, even if ray is outside of view

##### PSSM
- For directional lights, logarithmic splitting
- Might support depth dependent splitting at some time

##### Soft Shadow Penumbras
- With variance shadow maps (VSM)

##### SSSSS
- Screen space subsurface scattering
- Based on pregenerated light transport map

##### Multi-Hemisphere-Skybox

##### Atmospheric Scattering
- Based on the work of Eric Bruneton, but improved and adapted for non-spheres

##### Shadows
- Shadow updates delayed over multiple frames
- Shadow atlas, also dynamic resolution adaption

##### Lighting:
- Point Lights
    - Shadows via cubemap
- Directional Lights
    - PSSM Shadows, see above
- Ambient Lights
    - Darken or Bright
        - Artist controlled Global Illumination
- Projector Lights
    - Like a perspective lens
    - Projection texture
        - Can be used for flashlights for example
- Area Lights
    - Caster is a rectangle
    - Also supports projection texture
    - Shadows are computed by cone tracing (see GI)

##### Physically based shading / lighting

##### Tone mapping (HDR)
- Also artist controlled color correction

##### Blur
- Focal Blur
- Movement Blur (edges)
- Mipmap based + in place 4x4 kernel
    - Varying radius (DOF)
- Maybe Bokeh

##### Tesselation Shader displacement

##### Approximated Chromatic Aberration
