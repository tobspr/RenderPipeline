## Deferred Render Pipeline

**NOTE:** I recently created a new master to clean up the repositority. Please
use a clean checkout of the new master branch to continue to work with the pipeline!



This is my deferred render pipeline, implemented in Panda3D. This 
pipeline aims to handle the complete graphics pipeline, giving the user the 
ability to focus on making the game, and not the graphics.

**Forum Thread**: http://www.panda3d.org/forums/viewtopic.php?f=6&t=17050

This pipeline is still in developement, feel free to join :)

For questions & suggestions you can find me at `#panda3d` on freenode. 
Thanks especially to rdb and all the others for support & help!

### Installation & Usage

You can find the wiki & instructions how to setup the pipeline at
https://github.com/tobspr/RenderPipeline/wiki/Getting-Started

### Requirements

- OpenGL 4.3 capable GPU
- Panda3D Development Build ( https://github.com/panda3d/panda3d )
- 1GB Graphics Memory recommended (Can run with less, too)

### Features

##### Physically based shading
##### Deferred rendering
##### Order Independent Transparency
##### Temporal Ambient Occlusion
- SAO and HBAO

##### Tile based light culling

##### Realtime Global Illumination
- Light propagation volumes

##### Dynamic Scene Voxelization
- Coming soon: Voxel based light shafts

##### Screen Space Local Reflections

##### High quality Shadows
- PCF for PointLights, SpotLights
- PCSS for DirectionalLights
- PSSM Shadows for DirectionalLights

##### [Todo] Screen space subsurface scattering
##### Multi-Hemisphere-Skybox

##### [Coming soon] Dynamic volumetric clouds

##### Atmospheric Scattering

##### Supported Lights:
- Point Lights
- Directional Lights
- Spot Lights
- [Todo] Ambient Lights
- [Todo] Area Lights


##### Dynamic scene exposure
##### Color LUT, Chromatic Abberation, Grain and Sharpen
##### Blur
- [Todo] Bokeh DOF
- Per object and camera motion blur

##### Bloom

##### Tesselation


### Screenshots

You can find a lot more screenshots <a href="https://www.dropbox.com/sh/dq4wu3g9jwjqnht/AAABSOPnglDHZYsG5HXR-mhWa?dl=0">here</a>, or in the forum thread.

![Sponza](http://fs1.directupload.net/images/150813/eonuaryk.png)
![Terrain](http://fs1.directupload.net/images/150803/33uuhjc3.png)
![Couch Scene](http://fs2.directupload.net/images/150502/jl66b4cc.png)
