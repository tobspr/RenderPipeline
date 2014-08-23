
# No stack trace on assertion
assert-abort #f

# File system should be case sensitive
# NOTICE: Set this to #f if you are using tempfile. Because it returns
# wrong cased directory paths :(
vfs-case-sensitive #f

# Animations on the gpu
# hardware-animated-vertices #t

# Show error on dll loading
# show-dll-error-dialog #t

# Trying this for performance
# uniquify-matrix #f

# Garbarge collection
garbage-collect-states #t
# garbage-collect-states-rate 0.2


transform-cache #t
state-cache #t


# Trying this for performance
# uniquify-transforms #f
# uniquify-states #f 
# uniquify-attribs #f

# Faster texture loading
# fake-texture-image someimage.png

# Frame rate meter
frame-rate-meter-milliseconds #t
frame-rate-meter-update-interval 1.0
frame-rate-meter-text-pattern %0.2f fps
frame-rate-meter-ms-text-pattern %0.3f ms
frame-rate-meter-layer-sort 1000
frame-rate-meter-scale 0.04
frame-rate-meter-side-margins 0.4


# Pstats
pstats-target-frame-rate 30.0
# pstats-unused-states #f

# For smoother animations
# even-animation #t


# Threading
# threading-model App/Cull/Draw


# Try for better performance
# prefer-single-buffer #t

# No stencil
support-stencil #f
framebuffer-stencil #f


# Undecorated?
# undecorated #t

# Not resizable
win-fixed-size #t
# win-size 1616 976
win-size 1600 900
# win-size 1600 960
# win-size 1920 1080
# fullscreen #t
# win-size 1280 720

# Icon
# icon-filename lalala

# Show custom cursor
# cursor-filename lalala

# The title of the window
window-title Render Pipeline by tobspr 


# Framebuffers use SRGB
framebuffer-srgb #f

# Framebuffers need no multisamples
framebuffer-multisample #f
multisamples 0

# No V-Sync
sync-video #f


# Compress texture?
# driver-compress-textures #t


# Better performance for vertices??
# display-lists #t

# Faster animations??
# matrix-palette #tc
# display-list-animation #t

# Don't rescale textures which are no power-of-2
textures-power-2 none

# Dump shaders
# gl-dump-compiled-shaders #f
# notify-level-glgsg debug

# Better GL performance
gl-finish #f
gl-force-no-error #t
gl-check-errors #f
gl-force-no-flush #t
gl-force-no-scissor #t
gl-debug #t

# gl-enable-memory-barriers #f

text-minfilter linear
text-magfilter linear
text-page-size 128 128

show-frame-rate-meter #t

texture-anisotropic-degree 0
texture-magfilter linear
texture-minfilter linear
# 
# cache-models #f
# texture-cache #f

lock-to-one-cpu #f
support-threads #t

# driver-generate-mipmaps #f
# gl-ignore-mipmaps #t

gl-immutable-texture-storage #f

# notify-level-gobj debug

gl-dump-compiled-shaders #f

gl-cube-map-seamless #t

# buggy as hell
# want-directtools #t
# want-tk #t


model-cache-dir $USER_APPDATA/Panda3D-1.9/cache
model-cache-textures #f

notify-level-pnmimage error
show-buffers #f