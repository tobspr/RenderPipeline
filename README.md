## Deferred Render Pipeline *Version 2.0*

This is the second version of the Pipeline. If you are looking for the first
version, change to the `master` branch! The master branch was cleaned up a while ago,
if you are looking for even older versions, checkout the `old_master` branch.

<img src="http://i.imgur.com/Sj9xV3U.png" />

### Core Features

- Physically Based Shading
- Deferred Rendering
- Advanced Post-Processing
- Time of Day System
- Plugin System

### Requirements

- OpenGL 4.3 capable GPU
- Panda3D Development Build ( https://github.com/panda3d/panda3d )
- 1GB Graphics Memory recommended (Can run with less, too)

**Notice**: It seems that the drivers for Intel HD Graphics on Linux are not
capable of all 4.3 features, so the pipeline is not able to run there!

### Getting Started / Wiki

You should definitely checkout the wiki if you want to find out more about the pipeline:
<a target="_blank" href="https://github.com/tobspr/RenderPipeline/wiki">Render Pipeline WIKI</a>

There is also a page about getting started there: <a target="_blank" href="https://github.com/tobspr/RenderPipeline/wiki/Getting%20Started">Getting Started</a>



### Precompiled builds

If you want to use the C++ modules, but don't want to compile the modules yourself,
you can use a precompiled build from here:

<a target="_blank" href="https://www.dropbox.com/sh/maxpc6gouqzm9s8/AAAbK05FKpVF8SvT2eBPMpd9a?dl=0
">Precompiled-Builds on Dropbox</a>

Just copy it over to `Code/Native/RSNative.pyd`, you can run the
setup with `python setup.py --skip-native` then.
Those builds are getting uploaded whenever I build the pipeline on my machine, 
so they should be updated most of the time (*At least 64bit, if you need a fresh
32bit build, let me know*).


### Reporting Bugs / Contributing

If you find bugs, or find information missing in the wiki, or want to contribute,
you can find me most of the time in the `#panda3d` channel on freenode.

If I shouldn't be there, feel free to contact me per E-Mail: `tobias.springer1@googlemail.com`

---

<b>Further information about the pipeline can also be found at the website: <a href="http://tobspr.me/renderpipeline/" target="_blank">tobspr.me/renderpipeline/</a></b>