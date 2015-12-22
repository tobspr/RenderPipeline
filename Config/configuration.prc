
# ---------------  Window settings  --------------

fullscreen #f
win-size 1920 1080
window-title Render Pipeline by tobspr 
icon-filename Data/GUI/icon.ico

# --------------  Debugging options  --------------

# gl-dump-compiled-shaders #t
# notify-level-glgsg debug
# notify-level-gobj debug
notify-level-glgsg error
pstats-gpu-timing #t
gl-debug #t


# ----------------- Misc Settings -----------------

# No stack trace on assertion, set this to true to make panda crash on assertions
# (which will allow to debug it)
# assert-abort #f

# File system should be case sensitive
# NOTICE: Set this to #f if you are using tempfile, since it returns
# wrong cased directory paths
vfs-case-sensitive #f



# Enable state cache, this seems to actually help the performance by a lot
state-cache #t
transform-cache #t

# Frame rate meter style
show-frame-rate-meter #f
frame-rate-meter-milliseconds #t
frame-rate-meter-update-interval 1.0
frame-rate-meter-text-pattern %0.2f fps
frame-rate-meter-ms-text-pattern %0.3f ms
frame-rate-meter-layer-sort 1000
frame-rate-meter-scale 0.036
frame-rate-meter-side-margins 0.4

# Set text settings
text-minfilter linear
text-magfilter linear
text-page-size 512 512

# Better text performance since rdb's patch
text-flatten 0
text-dynamic-merge 1

# For smoother animations
# even-animation #t

# Threading, really buggy!
#threading-model App/Cull/Draw

support-stencil #f
framebuffer-stencil #f

# Don't use srgb correction, we do that ourself
framebuffer-srgb #f

# Don't use multisamples
framebuffer-multisample #f
multisamples 0

# Disable V-Sync
sync-video #f

# Don't rescale textures which are no power-of-2
textures-power-2 none

# This is required, the pipeline does not support resizing yet
win-fixed-size #t

# Set default texture filters
texture-anisotropic-degree 0
texture-magfilter linear
texture-minfilter linear

# Enable seamless cubemap filtering, thats important for environment filtering
gl-cube-map-seamless #t

# Set model cache dir
model-cache-dir $USER_APPDATA/Panda3D-1.9/cache
model-cache-textures #f

# Disable the annoying SRGB warning from pnmimage
notify-level-pnmimage error

# Disable the buffer viewer, we have our own
show-buffers #f

# Use the default coordinate system, this makes our matrix transformations 
# faster because we don't have have to transform them to a different coordinate
# system before
gl-coordinate-system default

# This makes animations smoother, especially if they were exported at 30 FPS
# and are played at 60 FPS
interpolate-frames 1

# Disable workarround in panda which causes our shadow atlas to take twice
# the amount of vram it should, due to an intel driver bug.
gl-force-fbo-color false


# ----------- OpenGL / Performance Settings ------------

# Set the minimum openGL version
gl-version 3 2

# Animations on the gpu. The default shader has to get adjusted to support this
# feature before this option can be turned on.
# hardware-animated-vertices #t

# Try this options for performance
# uniquify-transforms #t
# uniquify-states #t
# uniquify-attribs #f

# Enable garbarge collection
garbage-collect-states #t
# garbage-collect-states-rate 0.2

# Compress textures on the drivers?
# driver-compress-textures #t

# Faster animations? (Have to test)
# matrix-palette #t
# display-list-animation #t

# Better GL performance by not using gl-finish and so on
gl-finish #f
gl-force-no-error #t
gl-check-errors #f
gl-force-no-flush #t
gl-force-no-scissor #t

# Eventually disable memory barriers, have to check if this is faster
gl-enable-memory-barriers #f

# Disable threading
lock-to-one-cpu #t
support-threads #f

# Let the driver generate the mipmaps
driver-generate-mipmaps #t
#gl-ignore-mipmaps #t

# Use immutable texture storage, it is *supposed* to be faster, but might not be
gl-immutable-texture-storage #t

auto-flip #f
gl-debug-object-labels #t

# Default window settings
# depth-bits 0
color-bits 0

framebuffer-depth #f
