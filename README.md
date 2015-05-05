## Deferred Render Pipeline

This is my deferred render pipeline, implemented in Panda3D. This 
pipeline aims to handle the complete graphics pipeline, giving the user the ability to focus on making the game, and not the graphics.

**Forum Thread**: http://www.panda3d.org/forums/viewtopic.php?f=6&t=17050

This pipeline is still in developement, feel free to join :)

For questions & suggestions you can find me at #panda3d on freenode.
Thanks especially to rdb and all the others for support & help!

### Screenshots

You can find a lot more <a href="https://www.dropbox.com/sh/dq4wu3g9jwjqnht/AAABSOPnglDHZYsG5HXR-mhWa?dl=0">here</a>:

![Couch Scene](http://fs2.directupload.net/images/150502/jl66b4cc.png)
![Transparency Test](http://fs2.directupload.net/images/150503/78h7dpz9.png)
![BRDF Test #2](http://fs1.directupload.net/images/141222/9sgebqmw.png)
![Sponza](http://s7.directupload.net/images/140919/a6b3vyb5.png)


### Setup
You can find the wiki & instructions how to setup the pipeline at
https://github.com/tobspr/RenderPipeline/wiki

### Features

[Todo] means the feature is not implemented yet.

[Improve] means it is implemented, but has to get improved to look good.

###### Physically based shading / lighting
###### Deferred rendering
###### Order Independent Transparency
###### Temporal Ambient Occlusion
- SAO and HBAO

###### Realtime Global Illumination
- Voxel cone traced global illumination
- Cone traced specular reflections
- Cone traced low frequency ambient occlusion

###### Dynamic Scene Voxelization

###### [Improve] Screen Space Local Reflections

###### High quality Shadows
- PCF for PointLights, SpotLights
- PCSS for DirectionalLights
- PSSM Shadows for DirectionalLights

###### [Todo] Screen space subsurface scattering
###### Multi-Hemisphere-Skybox

###### Atmospheric Scattering

###### Supported Lights:
- Point Lights
- Directional Lights
- [Todo] Ambient Lights
- [Todo] Spot Lights
- [Todo] Area Lights

##### Color LUT, Dynamic Exposure and Chromatic Abberation
##### Blur
- [Todo] Bokeh DOF
- [Improve] Motion blur based on velocity

##### Tesselation

