[![Join the chat at https://gitter.im/tobspr/RenderPipeline](https://badges.gitter.im/tobspr/RenderPipeline.svg)](https://gitter.im/tobspr/RenderPipeline?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) 
[![Build Status](https://travis-ci.org/tobspr/RenderPipeline.svg?branch=master)](https://travis-ci.org/tobspr/RenderPipeline)
<!-- # Render Pipeline -->

<img src="http://i.imgur.com/PO4OK4a.png" alt="Deferred Rendering Pipeline with Physically Based Shading" />

Deferred Realtime Rendering Pipeline with Physically Based Shading for the <a href="http://github.com/panda3d/panda3d">Panda3D Game Engine</a>.

### Core Features

- Physically Based Shading
- Deferred Rendering
- Advanced Post-Processing Effects and Framework
- Time of Day System
- Plugin System

## Screenshots

You can click on the images to enlarge them. Besides of that, you can find many more screenshots in my <a href="https://www.dropbox.com/sh/dq4wu3g9jwjqnht/AAABSOPnglDHZYsG5HXR-mhWa" target="_blank">dropbox folder</a>.

**Forest**
<img src="http://i.imgur.com/fD88ZMU.png" />

**Material demo**
<img src="http://i.imgur.com/M5YtvYR.png" />

**Screen space reflections**
<img src="http://i.imgur.com/oOwLXAK.png" />

**Car rendering**
<img src="http://i.imgur.com/hFD4qjV.png" alt="Car rendering" />

**Plugin and Time of Day editor:**
<img src="http://i.imgur.com/a8VpiHS.png" />

**Terrain and volumetric clouds**
<img src="http://i.imgur.com/zE0ywPl.png" />


See the <a target="_blank" href="https://github.com/tobspr/RenderPipeline/wiki/Features">Feature List</a>
for a list of features, and list of techniques I intend to implement.

You can find my todo list for the render pipeline here: <a href="https://trello.com/b/Li2JQi0q/render-pipeline" target="_blank">Render Pipeline Roadmap</a>.

### Getting Started / Wiki

You should checkout the wiki if you want to find out more about the pipeline:
<a target="_blank" href="https://github.com/tobspr/RenderPipeline/wiki">Render Pipeline WIKI</a>

There is also a page about getting started there: <a target="_blank" href="https://github.com/tobspr/RenderPipeline/wiki/Getting%20Started">Getting Started</a>

### Requirements

- OpenGL 4.3 capable GPU (and drivers)
- <a target="_blank" href="https://github.com/panda3d/panda3d">Panda3D</a> Development Build
- 1 GB Graphics Memory recommended *(Can run with less, depends on enabled plugins and resolution)*

**Notice**: It seems that the drivers for Intel HD Graphics on Linux are not
capable of all 4.3 features, so the pipeline is not able to run there!

If you want to use the C++ Modules, checkout <a href="https://github.com/tobspr/RenderPipeline/wiki/Building%20the%20CPP%20Modules" target="_blank">
Building the C++ Modules</a> to get a list of requirements for them.

### Reporting Bugs / Contributing

If you find bugs, or find information missing in the wiki, or want to contribute,
you can find me most of the time in the `#panda3d` channel on freenode.

If I shouldn't be there, feel free to contact me per E-Mail: `tobias.springer1@googlemail.com`

